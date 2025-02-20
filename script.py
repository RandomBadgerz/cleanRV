import io
import re

import pandas as pd
import streamlit as st

# Set page configuration for wider layout
st.set_page_config(
    page_title="RealVision Clean",  # Title of the app (appears in the browser tab)
    page_icon=":bar_chart:",  # Optional: Emoji or string icon
    layout="wide"  # Key setting for making the app wider
)

# Title and header
col1, col2 = st.columns([1, 11])  # Two columns, adjust width ratio as needed

with col1:
    st.image("rvlogo.png", width=100)  # Adjust 'width' to reduce the size

    with col2:
        st.markdown(
            '<h1 style="background: linear-gradient(to right, #fec76f, red); -webkit-background-clip: text; color: transparent; font-weight: bold;">RealVision Cleaning App</h1>',
            unsafe_allow_html=True
        )
st.header("Upload Multiple Files, Select and Rename Columns, and Combine Them")

# Initialize session state to store the combined DataFrame, checkbox states, and column rename mappings
if "append_files_pressed" not in st.session_state:
    st.session_state.append_files_pressed = False  # Default to not pressed
if "clean_files_pressed" not in st.session_state:
    st.session_state.clean_files_pressed = False  # Default to not pressed
if "combined_df" not in st.session_state:
    st.session_state.combined_df = None
if "columns_to_include" not in st.session_state:
    st.session_state.columns_to_include = None
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None
if "checkbox_states" not in st.session_state:
    st.session_state.checkbox_states = {}
if "rename_columns" not in st.session_state:
    st.session_state.rename_columns = {}  # Stores column renaming mappings

# File uploader for multiple Excel or CSV files
uploaded_files = st.file_uploader("Upload your Excel or CSV files", type=["xlsx", "xls", "csv"],
                                  accept_multiple_files=True)

# Button to append and process files
if uploaded_files:
    st.write("Uploaded files:")
    for uploaded_file in uploaded_files:
        st.write(f"- {uploaded_file.name}")

    if st.button("Submit"):
        st.session_state.append_files_pressed = True  # Set state to True when button is pressed

    # Only run the block of code if the button was pressed
    if st.session_state.append_files_pressed:
        all_dataframes = []  # List to store DataFrames from each file
        mismatched_columns = []  # List to track files with mismatched columns
        file_row_counts = {}  # Dictionary to store row counts for each file

        base_columns = None  # Reference columns for validation

        for uploaded_file in uploaded_files:
            try:
                # Determine file type and load files accordingly
                if uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".xls"):
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    st.warning(f"File type of {uploaded_file.name} is not supported.")
                    continue

                # Count rows in the current file
                file_row_counts[uploaded_file.name] = len(df)  # Number of rows in the file

                # Base columns reference is set from the first file
                if base_columns is None:
                    base_columns = set(df.columns)

                # Check column consistency
                if set(df.columns) != base_columns:
                    mismatched_columns.append(uploaded_file.name)
                else:
                    all_dataframes.append(df)
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")

        # Display row counts for each file
        st.subheader("Uploaded File Information")
        for filename, row_count in file_row_counts.items():
            st.write(f"{filename}: {row_count} rows")

        # Handle mismatched files
        if mismatched_columns:
            st.warning("The following files have mismatched columns and were not included in the final table:")
            for file in mismatched_columns:
                st.write(f"- {file}")

        # Append all DataFrames together if column matches
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            st.session_state.combined_df = combined_df  # Store the DataFrame in session state

            st.success("All matching files have been successfully appended!")

        else:
            st.error("No files were appended. Please ensure uploaded files have matching columns.")

        # Display combined row counts
        total_rows = len(combined_df)
        st.write(f"Total Rows in Combined File: {total_rows}")


        if st.button("Clean"):
            st.session_state.clean_files_pressed = True  # Set state to True when button is pressed
        # Only run the block of code if the button was pressed
        if st.session_state.clean_files_pressed:
            #create final cleaned df based on the combined df
            cleaned_df = combined_df

            if 'published' in cleaned_df.columns:
                # Extract only the date
                cleaned_df['published'] = cleaned_df['published'].dt.date

            if 'tags_marking' in cleaned_df.columns:
                # filter non-checked row out
                cleaned_df = cleaned_df[cleaned_df["tags_marking"].str.contains("checked", na=False)]

            if 'tags_customer' in cleaned_df.columns:
                # filter hid row out
                cleaned_df = cleaned_df[~cleaned_df["tags_customer"].str.contains("Hide/hide", na=False)]

            if 'content' in cleaned_df.columns and 'title' in cleaned_df.columns:
                # add title to message
                cleaned_df['content'] = combined_df['title'].fillna('') + ' ' + cleaned_df['content'].fillna('')
                # cut content length to 750
                cleaned_df['content'] = cleaned_df['content'].str[:750]

            if 'url' in cleaned_df.columns:
                # cut url length to 750
                cleaned_df['url'] = cleaned_df['url'].str[:750]

            if 'sentiment' in cleaned_df.columns:
                # replace sentiment value
                cleaned_df['sentiment'] = cleaned_df['sentiment'].replace(5, 'Positive')
                cleaned_df['sentiment'] = cleaned_df['sentiment'].replace(0, 'Neutral')
                cleaned_df['sentiment'] = cleaned_df['sentiment'].replace(-5, 'Negative')

            if 'source_type' in cleaned_df.columns:
                # create source_dict
                source_dict = {
                    'SOCIALMEDIA,SOCIALMEDIA_TWITTER': 'X',
                    'SOCIALMEDIA,SOCIALMEDIA_FACEBOOK': 'Facebook',
                    'SOCIALMEDIA,SOCIALMEDIA_YOUTUBE': 'Youtube',
                    'SOCIALMEDIA,SOCIALMEDIA_INSTAGRAM': 'Instagram',
                    'ONLINENEWS,ONLINENEWS_OTHER': 'Website',
                    'ONLINENEWS,ONLINENEWS_NEWSPAPER': 'Website',
                    'BLOG,BLOG_OTHER': 'Website',
                    'ONLINENEWS,ONLINENEWS_PRESSRELEASES': 'Website',
                    'ONLINENEWS,ONLINENEWS_BLOG': 'Website',
                    'ONLINENEWS,ONLINENEWS_TVRADIO': 'Website',
                    'ONLINENEWS,ONLINENEWS_MAGAZINE': 'Website',
                    'SOCIALMEDIA,SOCIALMEDIA_LINEOA': 'Website',
                    'PODCAST,PODCAST_OTHER': 'Website',
                    'MESSAGEBOARD,MESSAGEBOARD_OTHER': 'Webboard',
                    'MESSAGEBOARD,MESSAGEBOARD_REDDIT': 'Webboard',
                    'ONLINENEWS,ONLINENEWS_AGENCY': 'Website'
                }

                # loop to change i in source_type to source dict accordingly
                for i in source_dict:
                    cleaned_df['source_type'] = cleaned_df['source_type'].replace(i, source_dict[i])

            #create column for each tags in tags_customer
            if 'tags_customer' in cleaned_df.columns:
                # Convert all non-string values to string
                cleaned_df['tags_customer'] = cleaned_df['tags_customer'].apply(lambda x: str(x) if not isinstance(x, str) else x)

                #collect all headtags
                new_column_header = []
                for row in cleaned_df['tags_customer']:
                    if row is not None and row != "" and isinstance(row, str):
                        new_column_header.extend(re.findall(r'(?:^|,)([^/]+)', row))


                #remove duplicate
                new_column_header = list(set(new_column_header))

                # Handle null values and create columns with corresponding tags
                for column in new_column_header:
                    cleaned_df[column] = cleaned_df['tags_customer'] \
                        .str.findall(r'{}/([^,]+)'.format(column)) \
                        .apply(lambda x: ', '.join(x) if isinstance(x, list) else '')

            #clean column name
            cleaned_df.columns = cleaned_df.columns.str.strip()
            cleaned_df.columns = cleaned_df.columns.str.lower()
            cleaned_df.columns = cleaned_df.columns.str.replace(' ', '_')
            # put cleaned_df in session so it does not reset
            st.session_state.cleaned_df = cleaned_df


            # Allow user to select columns to include and rename
            st.subheader("Select Columns to Include and Optionally Rename Them")

            columns = list(cleaned_df.columns)
            default_column = ['url', 'published','content','sentiment','source_type','category', 'extra_source_attributes.name','engagement']

            default_column = [item.strip() for item in default_column]
            default_column = [item.replace(" ", "_") for item in default_column]
            default_column = [item.lower() for item in default_column]

            # Placeholder for renaming and selection
            selected_columns = []

            # Check if the column name is in the mapping dict and set checkbox to True if matched
            column_name_mapping_dict = {
                'published': 'date',
                'source_type': 'channel',
                'extra_source_attributes.name': 'username',
                'engagement': 'total_engagement',
            }
            # For each column in the DataFrame
            for col in columns:
                # Ensure session state is initialized for checkbox states and text input values

                if col not in st.session_state.checkbox_states:
                    # Initialize checkbox state to False by default
                    st.session_state.checkbox_states[col] = False
                    if col in default_column:
                        st.session_state.checkbox_states[col] = True

                if col not in st.session_state.rename_columns:
                    st.session_state.rename_columns[col] = col  # Default to the original column name
                    st.session_state.rename_columns[col] = column_name_mapping_dict.get(col, col)

                # Create a horizontal layout with checkbox (left) and text input (right)
                col_checkbox, col_textbox = st.columns([1, 2])  # Adjust column widths for checkbox and text input

                # Add checkbox in the first column
                with col_checkbox:
                    st.session_state.checkbox_states[col] = st.checkbox(
                        f"{col}",
                        value=st.session_state.checkbox_states[col]  # Persist checkbox state in session_state
                    )

                # Add text input box in the second column for renaming
                with col_textbox:
                    # Only show text input if the column is selected
                    if st.session_state.checkbox_states[col]:
                        st.session_state.rename_columns[col] = st.text_input("temp",
                                                                             value=st.session_state.rename_columns[col],
                                                                             # Persist text input value in session_state
                                                                             key=f"text_input_{col}", # Ensure unique key for each text input
                                                                             label_visibility="hidden"  # Hide the label
                                                                             )

                # Collect the selected column and its new name (if applicable)
                if st.session_state.checkbox_states[col]:
                    selected_columns.append(col)

            # Store the selected columns in session state
            st.session_state.columns_to_include = selected_columns

            # Display the filtered and renamed DataFrame based on selected columns
            if selected_columns:
                # Apply renaming to the DataFrame
                rename_mapping = {col: st.session_state.rename_columns[col] for col in selected_columns}
                filtered_df = cleaned_df[selected_columns].rename(columns=rename_mapping)
                st.write("Sameple Result (With Renamed Columns):")
                st.dataframe(filtered_df.head(20))
            else:
                st.warning("No columns selected! Please select at least one column!")

        # Offer download if a combined DataFrame exists and columns are selected
        if st.session_state.cleaned_df is not None and st.session_state.columns_to_include:
            # Filter and rename the cleaned DataFrame
            rename_mapping = {col: st.session_state.rename_columns[col] for col in st.session_state.columns_to_include}

            filtered_cleaned_df = st.session_state.cleaned_df[st.session_state.columns_to_include].rename(
                columns=rename_mapping)

            # Export filtered combined DataFrame to an Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_cleaned_df.to_excel(writer, index=False, sheet_name='cleaned')
            processed_file = output.getvalue()

            # Add download button for Excel file
            st.download_button(
                label="Download Filtered Combined Excel File",
                data=processed_file,
                file_name="filtered_cleaned_files.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )