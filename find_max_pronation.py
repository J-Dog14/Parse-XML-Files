# This script will find the amount of pronation that is occurring in a pitcher 3 frames after ball release

import sqlite3
import os
import xml.etree.ElementTree as ET
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("prontaion.db")
cursor = conn.cursor()

# Create the pro table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        Max_Pronation_Z REAL
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()



# Set the NAME values and COMPONENT values you are looking for
variable_names_to_find = ["Release", "Pitching_Elbow_Angle"]
component_values_to_find = ["X", "Z"]


# Function to parse XML file and extract specific event data
def parse_xml(file_path, variable_names, component_values):
    tree = ET.parse(file_path)
    root = tree.getroot()

    data_values = {}

    for name_value, component_value in zip(variable_names, component_values):
        for component in root.findall(f'.//name[@value="{name_value}"]/component[@value="{component_value}"]'):
            data_attribute = component.get('data')

            # Split the data attribute value into a list of individual values
            values = data_attribute.split(',')

            # Convert each value to a float, handling 'nodata' cases
            float_values = []
            for value in values:
                if value.lower() == 'nodata':
                    float_values.append(float('nan'))
                else:
                    float_values.append(float(value))

            # Store the float values in the data dictionary
            key = f"{name_value}_{component_value}"
            data_values[key] = float_values

    return data_values


# Function to find Max_Pronation
def find_max_pronation(file_path):
    data_values = parse_xml(file_path, variable_names_to_find, component_values_to_find)

    # Extract time from the data
    release_time = data_values["Release_X"][0]

    # Calculate the frame index based on the capture rate
    capture_rate = 300
    release_frame = int(release_time * capture_rate)

    # Extract values from the data
    elbow_angle_z = data_values["Pitching_Elbow_Angle_Z"]

    # Find the Max_Pronation value, 3 frames after the release_frame
    try:
        max_pronation = elbow_angle_z[release_frame + 3]
    except IndexError:
        print("Not enough values after release frame to find Max_Pronation")
        return None

    return max_pronation


def update_database(file_name, max_pronation):
    # Connect to the SQLite database
    conn = sqlite3.connect("pronation.db")
    cursor = conn.cursor()

    try:
        print(f"File Name (XML): {file_name}")

        # Check if the file name exists in the pro table
        cursor.execute('SELECT * FROM pro WHERE file_name = ?', (file_name,))
        existing_record = cursor.fetchone()

        if existing_record:
            # Update the existing record
            cursor.execute('''
                UPDATE pro 
                SET Max_Pronation_Z=?
                WHERE file_name=?
            ''', (
                max_pronation,
                file_name,  # Update this line
            ))
        else:
            # Insert a new record
            print("Inserting new record:")
            print(f"File Name: {file_name}")
            print(f"Max Pronation: {max_pronation}")

            cursor.execute('''
                INSERT INTO pro (file_name, Max_Pronation_Z)
                VALUES (?, ?)
            ''', (
                file_name,  # Update this line
                max_pronation,
            ))

        # Commit the changes
        conn.commit()
        print("Database updated.")
        print(f"Rows affected: {cursor.rowcount}")

    finally:
        # Close the connection in the finally block to ensure it's closed even if an exception occurs
        conn.close()


# Make sure to update your directory to fit your needs
xml_files_directory = "C:\\Users\\Pronation"

for file_name in os.listdir(xml_files_directory):
    if file_name.endswith(".xml"):
        file_path = os.path.join(xml_files_directory, file_name)

        # Find Max_Pronation
        max_pronation = find_max_pronation(file_path)

        # Update data in the database
        update_database(file_name, max_pronation)

        # Display a confirmation message
        print(f"Data for file '{file_name}' updated in the database.")