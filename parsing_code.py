# Create a database
# Update database  variables and path to file as needed

import sqlite3
import xml.etree.ElementTree as ET
import os

# Connect to the SQLite database
conn = sqlite3.connect("varaibles.db")
cursor = conn.cursor()

# Drop the table if it exists
cursor.execute('DROP TABLE IF EXISTS variables')

# Create the variables table
cursor.execute('''
    CREATE TABLE variables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        Linear_Pelvis_Speed REAL,
        HSS_Footplant REAL,
    )
''')

# Commit the changes before proceeding to parsing XML files
conn.commit()

# List of XML files to parse (replace this with your actual directory path)
directory_path = "C:\\Users\\Data"

while True:
    # Get a list of XML files in the specified directory
    xml_files = [os.path.join(directory_path, file) for file in os.listdir(directory_path) if file.endswith(".xml")]

    # Track the number of new data entries
    new_data_entries = 0

    for file_name in xml_files:
        try:
            # Check if the file has already been processed
            cursor.execute('SELECT COUNT(*) FROM variables WHERE file_name = ?', (file_name,))
            count = cursor.fetchone()[0]

            if count == 0:
                # Parse the XML file
                tree = ET.parse(file_name)
                root = tree.getroot()

                # Extract and insert data into the database
                linear_pelvis_speed = None
                hss_footplant = None


                for variable_element in root.findall('.//name[@value]'):
                    variable_name = variable_element.attrib['value']
                    component_x_element = variable_element.find('./component[@value="X"]')
                    component_y_element = variable_element.find('./component[@value="Y"]')
                    component_z_element = variable_element.find('./component[@value="Z"]')

                    if variable_name == "MaxPelvisLinearVel_MPH" and component_y_element is not None:
                        linear_pelvis_speed = float(component_y_element.attrib['data'])
                    elif variable_name == "Hip Shoulders Sep@Footstrike" and component_z_element is not None:
                        hss_footplant = float(component_z_element.attrib['data'])

                # Insert the data into the database
                cursor.execute('''
                    INSERT INTO variables (
                        file_name,
                        Linear_Pelvis_Speed,
                        HSS_Footplant,
                    ) VALUES (?, ?, ?)
                ''', (file_name, linear_pelvis_speed, hss_footplant))

                # Increment the count of new data entries
                new_data_entries += 1

        except Exception as e:
            # Print the error and the file name where it occurred
            print(f"Error processing file {file_name}: {e}")

    # Commit the changes
    conn.commit()

    # If no new data entries, break out of the loop
    if new_data_entries == 0:
        break

# Close the connection
conn.close()

print("Data inserted into the database.")
