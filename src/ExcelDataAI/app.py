import streamlit as st
import pandas as pd
import duckdb
import os
from agent import app as agent_app

st.set_page_config(
    page_title="Executive Data AI", 
    page_icon="",
    layout="wide"
    )
# st.title("Executive Data Assistant")

def login_screen():
    """Returns True if the user is authenticated, False otherwise."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    # Login UI
    st.container()
    with st.columns([1, 2, 1])[1]: #center the login box
        st.title("Executive Data Assistant")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", width='stretch'):
            # Check against secrets.toml
            if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                st.session_state.authenticated = True
                st.session_state.user = username
                st.success(f"Welcome back, {username.upper()}!")
                st.rerun()
            else:
                st.error("Invalid username or passworrd.")
    return False


if not login_screen():
    st.stop()



DB_PATH = st.secrets["passwords"]["DB_PATH"]

# Initialize Database COnnection
def get_db_con():
    return duckdb.connect(DB_PATH)

def get_db_con_ro():
    return duckdb.connect(DB_PATH, read_only=True)

def get_all_tables():
    """Queries DuckDB to find all user-created tables."""
    with get_db_con_ro() as con:
        tables = con.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'main'
            """).fetchall()
    return [t[0] for t in tables]





# Initilize session state for file tracking
# if "file_catalog" not in st.session_state:
#     st.session_state.file_catalog = {} # {filename: table_name}

# Sidebar for setup
with st.sidebar:
    st.header("Data Management")
    
    # Multi-file Uploader
    uploaded_files = st.file_uploader(
        "Upload Excel Files",
        type=["xlsx", "xlsb"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            #table_name = uploaded_file.name.replace("xlsx","").replace(" ", "_").lower()
            base_name = uploaded_file.name.lower()
            for ext in [".xlsx", ".xlsb"]:
                base_name = base_name.replace(ext, "")
            
            table_name = base_name.replace(" ", "_").strip()

            with st.spinner(f"Ingesting {table_name}..."):
                try:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    df = pd.read_excel(temp_path, engine='calamine', dtype=str)

                    with get_db_con() as con:
                        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
                    
                    os.remove(temp_path)
                    st.toast(f"✅ Created DB table: {table_name}")
                
                except Exception as e:
                    st.error(f"XLSX to DB load failed: {e}")

    # if uploaded_files:
    #     for uploaded_file in uploaded_files:
    #         if uploaded_file.name not in st.session_state.file_catalog:
    #             with st.spinner(f"Processing file..."):
    #                 try:
    #                     # Clean table name (no spaces/dots)
    #                     table_name = uploaded_file.name.replace(".xlsx","").replace(" ","_").lower()
    #                     #Convert the file to parquet for better performance
    #                     temp_path = f"temp_{uploaded_file.name}"
    #                     with open(temp_path, "wb") as f:
    #                         f.write(uploaded_file.getbuffer())
    #                     df = pd.read_excel(uploaded_file, engine='calamine', dtype=str)
    #                     parquet_path = f"data/{tablex de3y_name}.parquet"
    #                     df.to_parquet(parquet_path)
                        
    #                     st.session_state.file_catalog[uploaded_file.name] = table_name
    #                     os.remove(temp_path)
    #                     st.toast(f"✅ {uploaded_file.name} is ready!")
    #                 except Exception as e:
    #                     st.error(f"Failed to load {uploaded_file.name}: {str(e)}")


        #st.success("Files processed!")

    st.write("---")
    st.subheader("Select Views")
    view_name = "dashboard"
    # sql_view = """
    # select "Project Id", "Project Name", "Project Billability", Practice, "Grade Name", "Utilization Location", 
    # "Customer ID", "Customer name", "ParentCustomerID", "Parent Customer", "Is Onsite", "BU", "SBU", "Geography",
    # "Market", "Market Unit",
    # "Billed FTE" 
    # from utilization_prediction_report;
    # """
    sql_view="""
            SELECT 
            t1."Project Id", 
            t1.Practice, 
            t1."Utilization Location" as Location, 
            t1."Grade Name" as Grade, 
            t1."Billed FTE Internal", 
            t1."Total FTE",
            COALESCE(demands.demand_count, 0) AS Demand,
            attr.attrition
        FROM utilization_prediction_report t1 
        LEFT JOIN (
            SELECT 
                "Project Id", 
                Practice, 
                Location, 
                "Grade HR", 
                COUNT(*) AS demand_count
            FROM demand_base
            GROUP BY "Project Id", Practice, Location, "Grade HR"
        ) demands 
        ON  t1."Project Id" = demands."Project Id" 
        AND t1.Practice = demands.Practice 
        AND t1."Utilization Location" = demands.Location 
        AND t1."Grade Name" = demands."Grade HR" 
        LEFT JOIN (
            SELECT 
                "Project Id", Practice, Location, Grade, 
                MAX("Count of ID") as attrition
            FROM np_jan26
            GROUP BY 1, 2, 3, 4
        ) attr 
            ON  t1."Project Id" = attr."Project Id" 
            AND t1.Practice = attr.Practice 
            AND t1."Utilization Location" = attr.Location 
            AND t1."Grade Name" = attr.Grade;
        """
    if st.button("Generate Report"):
        try:
            with get_db_con() as con:
                con.execute(f"CREATE OR REPLACE VIEW {view_name} AS {sql_view}")
            st.success(f"View '{view_name}' created!")
            st.rerun()
        except Exception as e:
            st.error(f"SQL Error: {e}")
        


    # Checkbox selection
    st.write("---")
    st.subheader("Select Tables")
    all_tables = get_all_tables()
    selected_tables = []

    if all_tables:
        for table in all_tables:
            col1, col2 = st.columns([0.8, 0.2])

            if col1.checkbox(f"{table}", value=False, key=f"chk_{table}"):
                selected_tables.append(table)

            # Delete button on the right
            # if col2.button("️", key=f"del_{table}", help=f"Delete {table} permanently", use_container_width=True):
            #     st.session_state.confirm_delete = table
            #     st.rerun()
            if col2.button("❌", key=f"del_{table}", type="secondary"):
                st.session_state.confirm_delete = table
                st.rerun()
        if "confirm_delete" in st.session_state:
            target = st.session_state.confirm_delete
            st.error(f"Are you sure you want to delete **{target}**?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, Delete", type="primary", width='stretch'):
                with get_db_con() as con:
                    con.execute(f'DROP TABLE "{target}"')
                del st.session_state.confirm_delete
                st.toast(f"Table {target} removed.")
                st.rerun()
            if c2.button("cancel", width='stretch'):
                del st.session_state.confirm_delete
                st.rerun
    else:
        st.info("No files exist. Upload a file to begin.")
    
    # Data Preview
    if selected_tables:
        with st.expander("Table Previews", expanded=False):
            with get_db_con_ro() as con:
                for table in selected_tables:
                    st.write(f"**{table}** (Top 5 rows)")
                    preview_df = con.execute(f"SELECT * FROM {table} LIMIT 1000").df()
                    st.dataframe(preview_df, width='stretch')
    if not selected_tables and all_tables:
        st.warning("Select tables to provide context to AI")

    # for file_name, table_name in st.session_state.file_catalog.items():
    #     if st.checkbox(f"{file_name}", value=True):
    #         selected_tables.append(table_name)
    # if selected_tables:
    #     with st.expander("Preview selected Data"):
    #         for table in selected_tables:
    #             preview_df = duckdb.query(f"SELECT * FROM 'data/{table}.parquet' LIMIT 5").to_df()
    #             st.write(f"Table: **{table}**")
    #             st.dataframe(preview_df)
    
    # if not selected_tables:
    #     st.warning("Select at least one file to start chatting.")
    




    # uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    # if uploaded_file:
    #     # Save file locally so duckdb can read it
    #     with open("data1.xlsx", "wb") as f:
    #         f.write(uploaded_file.getbuffer())
    #     st.success("File uploaded successfully & ready!") 
    # st.info("Using Gemini 2.5 flash, Update it for better results")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle Input
if prompt := st.chat_input("Ask a question about the selected data ..."):
    if not selected_tables:
        st.error("No data selected in the sidebar!")
    else:
        # Show user message
        st.session_state.messages.append({"role":"user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
    # Run the agent
    # if not os.path.exists("data/data1.xlsx"):
    #     st.error("Please upload as excel file first")
    # else:
        with st.chat_message("assistant"):
            status_container = st.status("Analyzing across files...", expanded=False)

            # Pass the list of selected tables to the agent
            inputs = {
                "question": prompt,
                "active_tables": selected_tables
            }
            

            try:
                # Stream the graph updates
                final_response = ""
                for step in agent_app.stream(inputs):
                    if "generate_query" in step:
                        status_container.write(f" User Question : {prompt}")
                        status_container.write(f" Generated SQL for : `{step['generate_query']['sql_query']}`")
                    # if "execute_query" in step:
                    #     status_container.write("Executed Query in DuckDB")
                    if "summerize" in step:
                        final_response = step['summerize']['messages'][0]
                
                status_container.update(label="Analysis Complete !", state="complete", expanded=False)
                st.markdown(final_response)

                st.session_state.messages.append({"role":"assistant", "content": final_response})
            
            except Exception as e:
                st.error(f"An error occurred: {e}")