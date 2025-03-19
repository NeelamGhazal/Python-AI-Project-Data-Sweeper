import streamlit as st
import pandas as pd
import os
from io import BytesIO


if 'processed_dfs' not in st.session_state:
    st.session_state.processed_dfs = {}

st.set_page_config(page_title="💽 Data Sweeper", layout='wide')
st.title("💽 Data Sweeper")
st.write("Transform your files between CSV and Excel formats with built-in data cleaning and visualization!")

uploaded_files = st.file_uploader("Upload your files (CSV or Excel):", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[-1].lower()
        file_key = file.name  
        
      
        if file_key not in st.session_state.processed_dfs:
            if file_ext == ".csv":
                st.session_state.processed_dfs[file_key] = pd.read_csv(file)
            elif file_ext == ".xlsx":
                st.session_state.processed_dfs[file_key] = pd.read_excel(file)
            else:
                st.error(f"Unsupported file type: {file_ext}")
                continue

        
        df = st.session_state.processed_dfs[file_key]

        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")
        st.write("🔍 Preview the Head of the Dataframe")
        st.dataframe(df.head())

        st.subheader("📊 Data Profiling")
        st.write(df.describe())

        st.subheader("⚒️ Data Cleaning Options")
        if st.checkbox(f"Clean Data for {file.name}", key=f"clean_{file_key}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Remove Duplicates from {file.name}", key=f"dup_{file_key}"):
                    df = df.drop_duplicates()
                    st.session_state.processed_dfs[file_key] = df  
                    st.write("Duplicates Removed!")
                    
                if st.button(f"Remove Outliers from {file.name}", key=f"out_{file_key}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    for col in numeric_cols:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        df = df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]
                    st.session_state.processed_dfs[file_key] = df  
                    st.write("Outliers Removed!")

            with col2:
                if st.button(f"Fill Missing Values for {file.name}", key=f"fill_{file_key}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                    st.session_state.processed_dfs[file_key] = df 
                    st.write("Missing Values have been Filled!")
                    
                if st.button(f"Trim String Columns for {file.name}", key=f"trim_{file_key}"):
                    string_cols = df.select_dtypes(include=['object']).columns
                    for col in string_cols:
                        df[col] = df[col].str.strip()
                    st.session_state.processed_dfs[file_key] = df  
                    st.write("String Columns Trimmed!")

        
        st.subheader("Select Columns to Convert")
        columns = st.multiselect(f"Choose Columns for {file.name}", df.columns, default=df.columns, key=f"cols_{file_key}")
        df = df[columns]
        st.session_state.processed_dfs[file_key] = df  

        
        st.subheader("Column Data Type Conversion")
        for idx, col in enumerate(df.columns):
            unique_key = f"dtype_{file_key}_{col}_{idx}"  
            data_type = st.selectbox(f"Convert {col} to", ["string", "number", "datetime"], key=unique_key)
            
            if st.button(f"Convert {col}", key=f"btn_{unique_key}"):
                try:
                    if data_type == "number":
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif data_type == "datetime":
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    else:
                        df[col] = df[col].astype(str)
                    st.session_state.processed_dfs[file_key] = df  
                    st.success(f"Column {col} converted to {data_type}!")
                except Exception as e:
                    st.error(f"Error converting {col}: {str(e)}")

        
        st.subheader("📊 Data Visualization")
        if st.checkbox(f"Show Visualization for {file.name}", key=f"viz_{file_key}"):
            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) >= 2:
                st.bar_chart(df[numeric_cols].iloc[:, :2])
            else:
                st.warning("Visualization requires at least 2 numeric columns.")

        
        st.subheader("🔁 Conversion Option")
        conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel"], key=f"conv_{file_key}")
        
        if st.button(f"Convert {file.name}", key=f"conv_btn_{file_key}"):
            buffer = BytesIO()
            if conversion_type == "CSV":
                df.to_csv(buffer, index=False)
                file_name = file.name.replace(file_ext, ".csv")
                mime_type = "text/csv"
            else:
                df.to_excel(buffer, index=False)
                file_name = file.name.replace(file_ext, ".xlsx")
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            buffer.seek(0)

            st.download_button(
                label=f"⬇️ Download {file.name} as {conversion_type}",
                data=buffer,
                file_name=file_name,
                mime=mime_type,
                key=f"dl_{file_key}"
            )

    st.success("🎉 All files processed!")  
