import streamlit as st
import pandas as pd
import pymysql

# Function to connect to the database
def get_connection():
    return pymysql.connect(host='localhost', user='root', passwd='1234', database='redbus')

# Fetch buses from the database based on the route and filter conditions
def fetch_buses(connection, from_location, to_location, filters):
    query = '''
        SELECT * FROM bus_routes 
        WHERE Route_Name LIKE %s AND Route_Name LIKE %s
    '''
    params = [f"%{from_location}%", f"%{to_location}%"]
    
    # Apply filters
    if filters['departure_time']:
        departure_time_filter = {
            'before 6am': 'Departing_Time < "06:00"',
            '6am to 12pm': 'Departing_Time BETWEEN "06:00" AND "12:00"',
            '12pm to 6pm': 'Departing_Time BETWEEN "12:00" AND "18:00"',
            'after 6pm': 'Departing_Time > "18:00"'
        }
        query += f" AND ({departure_time_filter[filters['departure_time']]})"
    
    if filters['bus_type']:
        query += " AND Bus_Type IN %s"
        params.append(tuple(filters['bus_type']))
    
    if filters['seat_availability']:
        query += " AND Seat_Availability >= %s"
        params.append(filters['seat_availability'])
    
    if filters['arrival_time']:
        arrival_time_filter = {
            'Before 6 am': 'Reaching_Time < "06:00"',
            '6 am to 12 pm': 'Reaching_Time BETWEEN "06:00" AND "12:00"',
            '12 pm to 6 pm': 'Reaching_Time BETWEEN "12:00" AND "18:00"',
            'After 6 pm': 'Reaching_Time > "18:00"'
        }
        query += f" AND ({arrival_time_filter[filters['arrival_time']]})"
    
    # Add price filter
    if filters['price_range']:
        query += " AND Price BETWEEN %s AND %s"
        params.append(filters['price_range'][0])
        params.append(filters['price_range'][1])
    
    df = pd.read_sql(query, connection, params=params)
    return df

# Fetch unique locations from the database
def fetch_locations(connection):
    query = '''
        SELECT DISTINCT Route_Name FROM bus_routes
    '''
    df = pd.read_sql(query, connection)
    # Extract all unique locations from Route_Name
    all_routes = df['Route_Name'].str.split(' to ').explode().unique()
    return all_routes

# Main function to display the app layout
def main():
    # Database connection
    connection = get_connection()

    # Title
    st.title('Easy and Secure Online Bus Tickets Booking')

    # Fetch location suggestions
    all_locations = fetch_locations(connection)
    all_locations = [''] + list(all_locations)  # Add an empty option as the default

    # Layout for From, To, and Search Buses filters
    col1, col2, col3 = st.columns([3, 3, 1])  # Adjust column width as needed for better alignment

    with col1:
        # Autocomplete for From location with blank as default
        from_location_input = st.selectbox(
            "Select From Location",
            options=all_locations,
            index=0,  # Set the default index to 0, which corresponds to the empty option
            key="from_select"
        )
        
    with col2:
        # Autocomplete for To location with blank as default
        to_location_input = st.selectbox(
            "Select To Location",
            options=all_locations,
            index=0,  # Set the default index to 0
            key="to_select"
        )
        
    with col3:
        search_button = st.button("Search Buses")

    # Sidebar filters
    st.sidebar.title('Filters')

    # Departure Time Filter
    departure_time = st.sidebar.selectbox(
        'Departure Time',
        options=['Any Time', 'before 6am', '6am to 12pm', '12pm to 6pm', 'after 6pm']
    )
    
    # Bus Type Filter
    bus_type = st.sidebar.multiselect(
        'Bus Type',
        options=[
            'SEATER', 
            'SLEEPER',
            'AC',
            'NONAC'
        ]
    )
    
    # Seat Availability Filter with Slider
    seat_availability_slider = st.sidebar.slider(
        'Minimum Seat Availability',
        min_value=0,  # Minimum value for the slider
        max_value=100,  # Maximum value for the slider, adjust as necessary
        value=0  # Default value
    )
    
    # Arrival Time Filter
    arrival_time = st.sidebar.selectbox(
        'Arrival Time',
        options=[
            'Any Time',
            'Before 6 am',
            '6 am to 12 pm',
            '12 pm to 6 pm',
            'After 6 pm'
        ]
    )
    # Price Range Filter with Slider
    min_price, max_price = st.sidebar.slider(
        'Price Range',
        min_value=0,  # Minimum value for the slider
        max_value=5000,  # Maximum value for the slider, adjust as necessary
        value=(0, 5000)  # Default value
    )
    # Map bus types to specific options
    bus_type_mapping = {
        'SEATER': [
            'INDRA (A.C. Seater)', 
            'A/C Seater / Sleeper (2+1)', 
            'Non A/C Seater / Sleeper (2+1)', 
            'NON A/C Seater (2+2)', 
            'Bharat Benz A/C Seater (2+2)', 
            'Super Luxury (Non AC Seater 2+2 Push Back)', 
            'LAHARI A/C SLEEPER CUM SEATER'
        ],
        'SLEEPER': [
            'STAR LINER (NON-AC SLEEPER 2+1)', 
            'A/C Sleeper (2+1)', 
            'NON A/C Sleeper (2+1)', 
            'Scania AC Multi Axle Sleeper (2+1)', 
            'Volvo Multi-Axle A/C Sleeper (2+1)', 
            'Volvo 9600 Multi-Axle A/C Sleeper (2+1)', 
            'VE A/C Sleeper (2+1)', 
            'Lahari Non A/C Sleeper Cum Seater'
        ],
        'AC': [
            'INDRA (A.C. Seater)', 
            'A/C Sleeper (2+1)', 
            'A/C Seater / Sleeper (2+1)', 
            'Scania AC Multi Axle Sleeper (2+1)', 
            'Volvo Multi-Axle A/C Sleeper (2+1)', 
            'Volvo 9600 Multi-Axle A/C Sleeper (2+1)', 
            'VE A/C Sleeper (2+1)', 
            'RAJDHANI (A.C. Semi Sleeper)', 
            'RAJADHANI AC (CONVERTED METRO LUXURY)', 
            'Rajdhani (AC Semi Sleeper 2+2)', 
            'GARUDA PLUS (VOLVO / BENZ A.C Multi Axle)', 
            'Bharat Benz A/C Sleeper (2+1)', 
            'Bharat Benz A/C Seater (2+2)', 
            'Electric A/C Seater (2+2)', 
            'Electric A/C Seater/Sleeper (2+1)'
        ],
        'NONAC': [
            'SUPER LUXURY (NON-AC, 2 + 2 PUSH BACK)', 
            'STAR LINER (NON-AC SLEEPER 2+1)', 
            'ULTRA DELUXE (NON-AC, 2+2 PUSH BACK)', 
            'NON A/C Seater / Sleeper (2+1)', 
            'NON A/C Sleeper (2+1)', 
            'NON A/C Hi-Tech (2+2)', 
            'NON A/C Hi-Tech Push Back (2+2)', 
            'NON A/C Semi Sleeper (2+2)', 
            'NON A/C Seater (2+2)', 
            'NON A/C Push Back (2+2)', 
            'Lahari Non A/C Sleeper Cum Seater'
        ]
    }

    # Convert selected bus types to the corresponding options
    selected_bus_types = []
    for bt in bus_type:
        selected_bus_types.extend(bus_type_mapping.get(bt, []))
    
    # Collect all filters
    filters = {
        'departure_time': departure_time if departure_time != 'Any Time' else None,
        'bus_type': selected_bus_types if selected_bus_types else None,
        'seat_availability': seat_availability_slider if seat_availability_slider > 0 else None,
        'arrival_time': arrival_time if arrival_time != 'Any Time' else None,
        'price_range': (min_price, max_price) if min_price != 0 or max_price != 10000 else None
    }

    # When the 'Search Buses' button is clicked
    if search_button:
        if from_location_input and to_location_input:
            # Fetch the filtered data
            df = fetch_buses(connection, from_location_input, to_location_input, filters)
            
            if not df.empty:
                st.write(f"Found {len(df)} buses")
                
                             # Define custom CSS for table styling
                st.markdown("""
                    <style>
                        .full-width-table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        .full-width-table th, .full-width-table td {
                            padding: 15px;
                            text-align: left;
                            border: none;
                        }
                        .full-width-table th {
                            background-color: #f4f4f4;
                            font-weight: bold;
                        }
                        .full-width-table tr:nth-child(even) {
                            background-color: #f9f9f9;
                        }
                        .full-width-table tr:nth-child(odd) {
                            background-color: #ffffff;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                # Display the table with custom styling
                table_html = df[['Bus_Name', 'Bus_Type', 'Departing_Time', 'Duration', 'Reaching_Time', 'Star_Rating', 'Price', 'Seat_Availability']].to_html(index=False, classes='full-width-table')
                st.write(table_html, unsafe_allow_html=True)
            else:
                st.write("No buses found.")
        else:
            st.write("Please select 'From Location' and 'To Location'.")

# Run the app
if __name__ == "__main__":
    main()