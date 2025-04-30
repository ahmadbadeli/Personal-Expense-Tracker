import streamlit as st
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import altair as alt
import time
import io



# static paths and variables
css_file_path = "styles.css"
file_path = "Expenses.csv"
is_filtered = False
columns_title = ["Date","Category","Amount","Note","ID"]
categories_path = "categories.csv"

# Limit length for text input
def limitTextLength(key, max_length):
    if len(st.session_state[key]) > max_length:
        st.session_state[key] = st.session_state[key][:max_length]

# Delete Row Function
def delRow(df, index, container, is_filtered, original_df):
    target_df = original_df if is_filtered else df
    
    if is_filtered:
        index = original_df[original_df["ID"].isin([df.at[index,"ID"]])].index[0]
    
    target_df = target_df.drop(index, axis=0).reset_index(drop=True)
    target_df.to_csv(file_path, index=False)
    
    tempMsg(container, "Row Deleted Successfully!")


# Edit Row Function
def editRow(df, index, container, is_filtered, original_df, *args):
    date, category, amount, note = args
    target_df = original_df if is_filtered else df
    if is_filtered:
        index = original_df[original_df["ID"].isin([df.at[index,"ID"]])].index[0]

    target_df.at[index, "Date"] = str(date)
    target_df.at[index, "Category"] = category
    target_df.at[index, "Amount"] = amount
    target_df.at[index, "Note"] = note
    target_df.to_csv(file_path, index=False)
    tempMsg(container, "Edited Successfully!")



# Show a Temporary Message in a Container 
def tempMsg(container,msg, mode=0):
    if mode ==0 :
        container.success(msg)
        time.sleep(1)
        container.empty()
    else:
        container.error(msg)
        time.sleep(2)
        container.empty()

# Write headers in columns
def writeColumns(columns,*args,mode=0):
    for column,arg in zip(columns,args):
        with column:
            if mode ==0:
                st.markdown(f"**{arg}**")
            else:
                st.markdown(arg)

# Create Edit and Delte Keys
def createActionButtons(col_delete, col_edit, index):
    edit_key = f"edit_{index}"
    delete_key = f"delete_{index}"

    with col_delete:
        st.button("❌", key=delete_key)
    with col_edit:
        st.button("📝", key=edit_key)

    return edit_key, delete_key

# open modal
def openModal(df, index, modal, is_filtered, original_df, categories):
    target_df = original_df if is_filtered else df
    if is_filtered:
        index = original_df[original_df["ID"].isin([df.at[index,"ID"]])].index[0]

    with modal.container():
        selected_row = target_df.iloc[index]
        date = st.date_input("Edit Date", value=selected_row["Date"], key="date-modal")
        category = st.selectbox("Edit Category", options=categories, index=categories.index(selected_row["Category"]), key="cat-modal")
        amount = st.number_input("Edit Amount", value=selected_row["Amount"], step=0.5, key="amount-modal")
        note = st.text_input("Edit Note (max: 35char)", value=selected_row["Note"], key="note-modal",on_change=limitTextLength,args=("note-modal",35,))
    
        col1, col2 = st.columns(2)

        with st.container(key="modal-buttons"):
            with col1:
                if st.button("Save", key="save-btn"):
                    # Save changes
                    target_df.at[index, "Date"] = str(date)
                    target_df.at[index, "Category"] = category
                    target_df.at[index, "Amount"] = amount
                    target_df.at[index, "Note"] = note
                    target_df.to_csv(file_path, index=False)
                    st.session_state["edit-modal-opened"] = False
                    st.rerun()
            with col2:
                if st.button("Cancel", key="cancel-btn"):
                    st.session_state["edit-modal-opened"] = False
                    st.rerun()
        
# Save categories with Temporary Message show
def saveCategoriesDf(new_categories,container):
            new_categories_df = pd.DataFrame({"Categories":new_categories})
            new_categories_df.to_csv("categories.csv",index=False)
            tempMsg(container,"Category Removed Successfully")
            st.rerun(scope="app")
