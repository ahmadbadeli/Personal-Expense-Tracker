import streamlit as st
import pandas as pd
from datetime import datetime
import os, time, io
import matplotlib.pyplot as plt
import altair as alt
from functions import delRow, editRow, tempMsg, writeColumns, createActionButtons, openModal, limitTextLength, saveCategoriesDf
from functions import css_file_path, file_path, is_filtered, columns_title, categories_path
from uuid import uuid4 as uuid
from streamlit_modal import Modal
import plotly.express as px


st.set_page_config(page_title="Budget Tracker", page_icon="💰",initial_sidebar_state="expanded")
st.title("💰 Personal Budget Tracker")

# create modal
modal = Modal(key="edit-modal", title="Edit Row")

#test some features

#CSS
with open(css_file_path, "r", encoding="utf-8") as file:
    css_content = file.read()
st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


# Load or initialize data
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
else:
    df = pd.DataFrame(columns=columns_title)

# Load or initialize categories
if os.path.exists(categories_path):
    categories_df = pd.read_csv("categories.csv")
    categories = list(categories_df["Categories"])
else:
    categories_df = pd.DataFrame({"Categories":["Food","Transport","Utilities","Other"]})
    categories = list(categories_df["Categories"])
    categories_df.to_csv(categories_path)

# Check Data Frame with new categories
indices_not_in_categories = [i for i, item in enumerate(list(df["Category"])) if item not in categories]
if indices_not_in_categories:
    df = df.drop(indices_not_in_categories,axis=0)
    df.to_csv(file_path,index=False)   

# Add Expense Form
with st.form(key="myForm"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", value=datetime.today())
        category = st.selectbox("Category", categories)
    with col2:
        amount = st.number_input("Amount", value=0.0, step=0.5)
        note = st.text_input("Note (max: 35char)",key="input-text")

    if st.form_submit_button("Add Expense"):
        if len(note) > 35:
            note = note[:35]

        new_df = pd.DataFrame([{"Date": date, "Category": category, "Amount": amount, "Note": note, "ID":str(uuid())}])
        df = pd.concat([df,new_df],ignore_index=True)
        df.to_csv(file_path,index=False)
        addContainer = st.empty()
        tempMsg(addContainer,"Expense Added Successfully!")

#assign filter variables
is_filtered = False
original_df = df.copy()

# add or remove a category
with st.expander("Add or Remove a Category"):
    with st.container(key="add-remove-category"):
        st.markdown("##### Add or Remove a Category")
        msg = st.empty()
        cols = st.columns([2,1,2,1])
        # Add a Category
        with cols[0]:
            new_category = st.text_input("New Category:")
        with cols[1]:
            if st.button("Add",key='add-category'):
                if new_category.lower() in [x.lower() for x in categories]:
                    tempMsg(msg,"Category already existed. Please enter a different category",mode=1)
                    
                else:
                    new_category = new_category.capitalize()
                    categories.append(new_category)
                    saveCategoriesDf(categories,msg)
            
        # Remove a category
        with cols[2]:
            selected_category = st.selectbox("Select a Category",options=categories)
        with cols[3]:
            if st.button("Delete",key="remove-category"):
                if len(categories) > 1:
                    categories.remove(selected_category)
                    saveCategoriesDf(categories,msg)
                else:
                    tempMsg(msg,"There is only 1 category left. If you want to delete this category please add another one",mode=1)       

# Filter Section
if not df.empty:  
    with st.expander("Filter data"):    
        with st.container(key="filterContainer"):
            st.markdown("<h5>Filter by Category and Date and Note</h5>",unsafe_allow_html=True)
            #Filetr by Category
            category_filter = st.multiselect("Filter by Category", options=df["Category"].unique())
            if category_filter:
                df = df[df["Category"].isin(category_filter)]
                is_filtered = True

            #Filter by Date
            df["Date"] = pd.to_datetime(df["Date"])
            original_df["Date"] = pd.to_datetime(original_df["Date"])

            start_date = st.date_input("Start Date", value=df["Date"].min())
            end_date = st.date_input("End Date", value=df["Date"].max())
            df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

            if start_date != original_df["Date"].min() or end_date != original_df["Date"].max():
                is_filtered = True

            # Filter by Note or Search for Note
            search_term = st.text_input("Search in notes")
            if search_term:
                df = df[df["Note"].str.contains(search_term, case=False, na=False)]
                is_filtered = True

            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")




    # Sort Table
    with st.container(key="sortSection"):
        st.markdown("<h5 style='text-align:center;'>Sort Data Table</h5>",unsafe_allow_html=True)
        cols = st.columns(2)
        with cols[0]:
            sort_by = st.selectbox("Sort by", options=["Date", "Amount", "Category"], index=0)
        with cols[1]:
            sort_order = st.radio("Order", options=["Ascending", "Descending"], horizontal=True)
            
        df = df.sort_values(by=sort_by, ascending=(sort_order == "Ascending")).reset_index(drop=True)
        original_df = original_df.sort_values(by=sort_by, ascending=(sort_order == "Ascending")).reset_index(drop=True)

        original_df.to_csv(file_path,index=False)

    # Download Filtered File
    with st.container(key="downloadFiles"):
        st.markdown("#### Download Filtered Data")
        downloadCols = st.columns(2)
        #Download CSV file
        with downloadCols[0]:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="expenses.csv",
                mime="text/csv",
                help="Download your expense data as CSV"
            )
        #Download Excel File
        with downloadCols[1]:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="auto") as writer:
                df.to_excel(writer, index=False, sheet_name="Expenses")
            buffer.seek(0)

            st.download_button(
                label="📥 Download Excel",
                data=buffer,
                file_name="expenses.xlsx",
                help="Download your expense data as Excel"
            )

    # Delete Row (Dropdown)
    with st.expander("Delte by select a row"):
        delContainer = st.empty()
        if not df.empty:
            with st.container(key="delRowContainer"):
                st.markdown("<h5>Delete by Row</h5>",unsafe_allow_html=True)
                col1, col2 = st.columns([3, 1.1])
                rowDisp = [f"{i+1}: {row['Category']} in {row['Date']} for ${row['Amount']:.2f} | {row['Note']}" for i, row in df.iterrows()]
                rowNum = col1.selectbox("Select Row", df.index, format_func=lambda x: rowDisp[x],key="selectDelete")
                col2.button("Delete Selected Row", key="delRowBtn", on_click=delRow,args=(df,rowNum,delContainer,is_filtered,original_df))

    # Edit Row (Dropdown)
    with st.expander("Edit by select a row"):
        editContainer = st.empty()
        if not df.empty:
            with st.container(key="editContainer"):
                st.markdown("##### Edit Row")
                col1, col2 = st.columns([5, 1])
                rowDisp = [f"{i+1}: {row['Category']} in {row['Date']} for ${row['Amount']:.2f} | {row['Note']}" for i, row in df.iterrows()]
                rowNum = col1.selectbox("Select Row", df.index, format_func=lambda x: rowDisp[x],key="selectEdit")
                selected_row = df.iloc[rowNum]
                new_date = st.date_input("Edit Date", value=selected_row["Date"])
                new_category = st.selectbox("Edit Category", categories,index=categories.index(selected_row["Category"]))
                new_amount = st.number_input("Edit Amount", value=selected_row["Amount"],step=0.5)
                new_note = st.text_input("Edit Note (max: 35char)", value=selected_row["Note"], key="edit-row-note",on_change=limitTextLength,args=("edit-row-note",35,))
                newDf = [new_date,new_category,new_amount,new_note]
                col2.button("Edit Row", key="editRowBtn", on_click=editRow,args=(df,rowNum,editContainer,is_filtered,original_df,*newDf))


    # Expenses Table
    delContainer = st.empty()
    editContainer = st.container()
    # sory by Category view
    if sort_by == "Category":
        st.markdown("#### Your Expenses")
        grouped = df.groupby("Category")

        for category, group in grouped:
            with st.expander(f"{category} ({len(group)} items)", expanded=True):
                # Column headers
                cols = st.columns([2, 2, 3, 1])
                headers = ["Date", "Amount", "Note", "Delete"]
                writeColumns(cols,*headers)
                
                # Rows
                for i, row in group.iterrows():
                    cols = st.columns([2, 2, 2, 1,1])
                    writeColumns(cols[0:3],row["Date"],f"${row['Amount']:.2f}",row["Note"],mode=1)
                    #Edit and Delete Functions:
                    edit_key, delete_key = createActionButtons(*cols[3:],i)
                    delete_index = int(str(delete_key)[7:])
                    edit_index = int(str(edit_key)[5:])

                    if st.session_state.get(edit_key):
                        editContainer.success(f"Editing row {edit_index}")

                    # Delete Function"                         
                    if st.session_state.get(delete_key):
                        delRow(df, delete_index, delContainer, is_filtered, original_df)
                        st.session_state.pop(delete_key, None)
                        st.rerun(scope="app")

                    # Edit Function"                         
                    if st.session_state.get(edit_key):
                        st.session_state.modal_row_idx = i
                        st.session_state["edit-modal-opened"] = True
                        st.session_state.pop(edit_key)
        # Total
        st.markdown(f"### 💰 Total Spent: **${df['Amount'].sum():.2f}**")

    else:
        with st.container(key="outputContainer"):
            editContainer = st.container()
            delContainer = st.empty()
            st.markdown("#### Your Expenses")
            # Draw Table
            cols = st.columns([1.5, 1.5, 1.5, 4, 1, 1])
            headers = ["Date", "Category", "Amount", "Note", "Delete", "Edit"]
            writeColumns(cols,*headers)

            for i in df.index:
                writeColumns(cols[0:4],df.at[i, "Date"],df.at[i, "Category"],f"${df.at[i, 'Amount']:.2f}",df.at[i, "Note"],mode=1)
                #Edit and Delete Functions:
                edit_key, delete_key = createActionButtons(*cols[4:],i)
                delete_index = int(str(delete_key)[7:])
                edit_index = int(str(edit_key)[5:])

                if st.session_state.get(edit_key):
                    editContainer.success(f"Editing row {edit_index}")

                # Delete Function"                         
                if st.session_state.get(delete_key):
                    delRow(df, delete_index, delContainer, is_filtered, original_df)
                    st.session_state.pop(delete_key, None)
                    st.rerun(scope="app")
                   
                # Edit Function"                         
                if st.session_state.get(edit_key):
                    st.session_state.modal_row_idx = i
                    st.session_state["edit-modal-opened"] = True
                    st.session_state.pop(edit_key)
                


            # Total
            st.markdown(f"### 💰 Total Spent: **${df['Amount'].sum():.2f}**")

    # Show Charts
    chart_type = st.selectbox("Chart Type:",options=["Matplotlib","Altair","Plotly"],index=2)
    if chart_type == "Altair":
        # Altair
        chart = alt.Chart(df).mark_arc().encode(
        theta=alt.Theta(field="Amount", type="quantitative"),
        color=alt.Color(field="Category", type="nominal"),
        tooltip=["Category", "Amount"])
        st.altair_chart(chart, use_container_width=True)
    elif chart_type == "Matplotlib":
        # Matplotlib
        fig, ax = plt.subplots()
        df_grouped = df.groupby("Category")["Amount"].sum()
        ax.pie(df_grouped, labels=df_grouped.index, autopct='%1.2f%%', startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
        st.info("Figures take about 20sec to upload/refresh. for faster chart switch to Altair")
    elif chart_type == "Plotly":
        fig = px.pie(df,names="Category",values="Amount",title="Amount by Category")
        st.plotly_chart(fig)

else:
    st.info("No expenses added yet.")

# Modal Edit
if st.session_state.get("edit-modal-opened", False):
    openModal(df, st.session_state["modal_row_idx"], modal, is_filtered, original_df, categories)