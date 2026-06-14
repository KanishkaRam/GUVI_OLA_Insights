import pandas as pd
import streamlit as st
import mysql.connector
from PIL import Image
from streamlit_option_menu import option_menu

# =======  MySQL Connection  ======
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="OlaRideInsight"
)

cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM ola_bookings")
record_count = cursor.fetchone()[0]

if record_count == 0:
    # =========== Read Excel File =========
    path = r"C:\Users\RAaM\OneDrive\Desktop\OLA Ride\OLA_DataSet.xlsx"
    df = pd.read_excel(path)

    # ======= DATA CLEANING ========

    # Fill cancellation-related columns
    cols = [
        'Canceled_Rides_by_Customer',
        'Canceled_Rides_by_Driver',
        'Incomplete_Rides',
        'Incomplete_Rides_Reason'
    ]
    df[cols] = df[cols].fillna('Not Applicable')

    # Fill Payment Method
    df['Payment_Method'] = df['Payment_Method'].fillna('Unknown')

    # Fill Numeric Columns
    numeric_cols = [    
        'V_TAT',
        'C_TAT',
        'Driver_Ratings',
        'Customer_Rating'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        median_value = df[col].median()
        df[col] = df[col].fillna(median_value)

    # ========= Save Cleaned CSV =========
    df.to_csv("ola_bookings_cleaned.csv", index=False)


    # ====  Convert NaN to None  =====
    df = df.where(pd.notnull(df), None)

    # =======  Prepare Data  =======
    data = [tuple(row) for row in df.to_numpy()]

    # ======= Insert into MySQL ========
    insert_query = """
    INSERT IGNORE INTO ola_bookings (
        Date,
        Time,
        Booking_ID,
        Booking_Status,
        Customer_ID,
        Vehicle_Type,
        Pickup_Location,
        Drop_Location,
        V_TAT,
        C_TAT,
        Canceled_Rides_by_Customer,
        Canceled_Rides_by_Driver,
        Incomplete_Rides,
        Incomplete_Rides_Reason,
        Booking_Value,
        Payment_Method,
        Ride_Distance,
        Driver_Ratings,
        Customer_Rating,
        Vehicle_Images
    )
    VALUES (
        %s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s
    )
    """
    cursor.executemany(insert_query, data)
    connection.commit()
    print(f"\n{cursor.rowcount} records inserted successfully!")


#======= Streamlit Page Design ==========

st.title('**OLA RIDE INSIGHTS**')
img = Image.open(r"C:\Users\RAaM\OneDrive\Desktop\OLA Ride\OLA_LOGO.png")
st.image(img,  width=350 )

with st.sidebar:
    selected = option_menu(
        "INSIGHTS",
        ["Home", "Successful Bookings", "Average Ride Distance", "Cancelled Rides", "Customers With Highest Ride Cancellation", "Rides Cancelled by Drivers", "Driver's Rating", "UPI Rides", "Average Customer Rating", "Total booking value", "Incomplete Rides"],
        default_index=0
    )

if selected == "Home":
    st.text(" ")
    st.text("OLA, a leading ride-hailing service, generates vast amounts of data related to ride bookings, driver availability, fare calculations, and customer preferences. To enhance operational efficiency, improve customer satisfaction, and optimize business strategies, this project focuses on analyzing OLA’s ride-sharing data.")
    st.text("The project will involve cleaning and processing raw ride data, performing exploratory data analysis (EDA), developing a dynamic Power BI dashboard, and creating a Streamlit-based web application to present key findings in an interactive and user-friendly manner.")

elif selected == "Successful Bookings":
    st.subheader("RETRIEVE ALL SUCCESSFUL BOOKINGS")
    st.text(
        "This section displays all ride bookings that were completed successfully. "
        "Analyzing successful bookings helps identify ride demand, customer usage patterns,revenue trends, and overall operational performance.")

    # Get total number of successful bookings
    count_query = "SELECT COUNT(*) FROM ola_bookings  WHERE Booking_Status = 'Success';"
    cursor.execute(count_query)
    total_records = cursor.fetchone()[0]
    st.metric("Total Successful Bookings", f"{total_records:,}")

    # Pagination settings
    page_size = 100
    total_pages = (total_records + page_size - 1) // page_size
    page_number = st.selectbox("Select Page", range(1, total_pages + 1))
    
    offset = (page_number - 1) * page_size

    # Fetch only records for the selected page
    query = f"""
        SELECT BOOKING_ID,  CUSTOMER_ID, VEHICLE_TYPE, PICKUP_LOCATION, DROP_LOCATION
        FROM ola_bookings
        WHERE Booking_Status = 'Success'
        LIMIT {page_size} OFFSET {offset};"""
    cursor.execute(query)
    data = cursor.fetchall()

    df = pd.DataFrame(data, columns=["BOOKING_ID","CUSTOMER_ID","VEHICLE_TYPE","PICKUP_LOCATION","DROP_LOCATION" ])
    st.write(f"Showing records {offset + 1} to "  f"{min(offset + page_size, total_records)} "f"of {total_records:,}"  )
    st.dataframe(df, use_container_width=True)

elif selected == "Average Ride Distance":
    st.subheader("RETRIEVE THE AVERAGE RIDE DISTANCE FOR EACH VEHICLE TYPE")
    st.text("This section analyzes the average ride distance covered by each vehicle type. "
    "Comparing average trip lengths across vehicle categories helps identify customer preferences,vehicle utilization patterns, and demand trends. These insights can support fleet management, "
    "pricing strategies, and operational planning.")
    query ="""SELECT VEHICLE_TYPE, ROUND(AVG(Ride_Distance), 2) AS AVG_DISTANCE
                FROM ola_bookings
                GROUP BY VEHICLE_TYPE
                ORDER BY VEHICLE_TYPE ASC;
                """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data,  columns=["VEHICLE_TYPE","AVG_DISTANCE"] )
    st.table(df)

elif selected == "Cancelled Rides":
    st.subheader("GET THE TOTAL NUMBER OF CANCELLED RIDES BY CUSTOMERS")
    st.text("This section displays the total number of rides cancelled by customers.These insights can be used to improve customer satisfaction and reduce cancellation frequency.")


    count_query = """SELECT COUNT(*) AS Customer_Cancellations
                    FROM ola_bookings
                    WHERE Booking_Status='Canceled by Customer';"""
    cursor.execute(count_query)
    total_records = cursor.fetchone()[0]
    st.metric(" NO OF RIDES CANCELLED BY CUSTOMERS", f"{total_records:,}")

elif selected == "Customers With Highest Ride Cancellation":
    st.subheader("LIST THE TOP 5 CUSTOMERS WHO BOOKED THE HIGHEST NUMBER OF RIDES")
    st.text("This analysis identifies the five customers with the highest ride booking frequency.These insights can support targeted marketing campaigns, reward programs, and customer retention strategies.")


    query = """SELECT Customer_ID, count(*) as No_of_Rides
                FROM ola_bookings
                GROUP BY Customer_ID
                ORDER BY No_of_Rides DESC
                LIMIT 5;
                """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data,  columns=["CUSTOMER_ID","NO.OF.RIDES"] )
    st.table(df)

elif selected == "Rides Cancelled by Drivers":
    st.subheader("GET THE NUMBER OF RIDES CANCELLED BY DRIVERS DUE TO PERSONAL AND CAR-RELATED ISSUES")
    st.text("This analysis calculates the total number of rides cancelled by drivers because of personal reasons or vehicle-related issues.The insights can be used to improve driver support, vehicle maintenance processes, and overall customer satisfaction.")

    count_query = """SELECT COUNT(*) AS Customer_Cancellations
                FROM ola_bookings
                WHERE Booking_Status='Canceled by Driver'  AND Canceled_Rides_by_Driver ='Personal & Car related issue';
                """
    cursor.execute(count_query)
    total_records = cursor.fetchone()[0]
    st.metric(" NO OF RIDES CANCELLED BY DRIVERS DUE TO PERSONAL AND CAR-RELATED ISSUES", f"{total_records:,}")

elif selected == "Driver's Rating":
    st.subheader("FIND THE MAXIMUM AND MINIMUM DRIVER RATINGS FOR PRIME SEDAN BOOKINGS")
    st.text("This analysis retrieves the highest and lowest driver ratings recorded for Prime Sedan bookings. These insights can support performance monitoring, driver training initiatives, and service quality improvements.")

    query = """SELECT Vehicle_Type,MAX(Driver_Ratings) AS MAXIMUM_RATING ,MIN(Driver_Ratings) AS MINIMUM_RATING
                FROM ola_bookings
                WHERE Vehicle_Type ='Prime Sedan';
                """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data,  columns=["VEHICLE_TYPE","MAXIMUM_RATING","MINIMUM_RATING"] )
    st.table(df)

elif selected == "UPI Rides":
    st.subheader("RETRIEVE ALL RIDES WHERE PAYMENT WAS MADE USING UPI")
    st.text("This analysis displays all ride bookings for which the payment method was UPI.These insights can support payment strategy decisions and enhance the overall customer payment experience.")

    # Get total number of rides with UPI Payment Method
    count_query = "SELECT COUNT(*) FROM ola_bookings  WHERE Payment_Method ='UPI';"
    cursor.execute(count_query)
    total_records = cursor.fetchone()[0]
    st.metric("Total Rides with UPI Payments", f"{total_records:,}")

    # Pagination settings
    page_size = 100
    total_pages = (total_records + page_size - 1) // page_size
    page_number = st.selectbox("Select Page", range(1, total_pages + 1))
    
    offset = (page_number - 1) * page_size

    # Fetch only records for the selected page
    query = f""" SELECT Booking_ID,Customer_ID,Vehicle_Type,Pickup_Location,Drop_Location,Booking_Value,Ride_Distance FROM ola_bookings
        WHERE Payment_Method ='UPI'
        LIMIT {page_size} OFFSET {offset};"""
    cursor.execute(query)
    data = cursor.fetchall()

    df = pd.DataFrame(data,  columns=["BOOKING_ID","CUSTOMER_ID","VEHICLE_TYPE","PICKUP_LOCATION","DROP_LOCATION","BOOKING_VALUE","RIDE_DISTANCE"] )
    st.write(f"Showing records {offset + 1} to "  f"{min(offset + page_size, total_records)} "f"of {total_records:,}"  )
    st.dataframe(df, use_container_width=True)

elif selected == "Average Customer Rating":
    st.subheader("FIND THE AVERAGE CUSTOMER RATING PER VEHICLE TYPE")
    st.text("This analysis calculates the average customer rating for each vehicle type. Comparing ratings across vehicle categories helps evaluate customer satisfaction levels, identify high-performing services, and understand customer preferences.")

    query = """SELECT Vehicle_Type, ROUND(AVG(Customer_Rating),2) AS AVG_CUSTOMER_RATING
                FROM ola_bookings
                GROUP BY Vehicle_Type
                ORDER BY Vehicle_Type;
                """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data,  columns=["VEHICLE_TYPE","AVG_CUSTOMER_RATING"] )
    st.table(df)

elif selected == "Total booking value":
    st.subheader("CALCULATE THE TOTAL BOOKING VALUE OF RIDES COMPLETED SUCCESSFULLY")
    st.text("This analysis computes the total booking value generated from rides that were completed successfully. Measuring revenue from completed rides helps assess business performance, track earnings, and evaluate operational efficiency.")

    query = """SELECT SUM(Booking_Value) AS TOTAL_BOOKING_VALUE 
                FROM ola_bookings
                WHERE Booking_Status ='Success' ;
                """
    cursor.execute(query)
    total_records = cursor.fetchone()[0]
    st.metric("THE TOTAL BOOKING VALUE OF RIDES COMPLETED SUCCESSFULLY", f"{total_records:,}")

elif selected == "Incomplete Rides":
    st.subheader("LIST ALL INCOMPLETE RIDES ALONG WITH THE REASON")
    st.text("This analysis retrieves all rides that were not completed and displays the corresponding reason for each incomplete booking.These insights can support process improvements, reduce ride cancellations, and enhance overall service reliability.")

    # Get total number of incomplete rides
    count_query = "SELECT COUNT(*) FROM ola_bookings  WHERE Incomplete_Rides ='Yes';"
    cursor.execute(count_query)
    total_records = cursor.fetchone()[0]
    st.metric("Total Incomplete_Rides", f"{total_records:,}")

    # Pagination settings
    page_size = 100
    total_pages = (total_records + page_size - 1) // page_size
    page_number = st.selectbox("Select Page", range(1, total_pages + 1))
    
    offset = (page_number - 1) * page_size

    # Fetch only records for the selected page
    query = f"""
        SELECT Booking_ID,Incomplete_Rides_Reason
        FROM ola_bookings
        WHERE Incomplete_Rides ='Yes'
        LIMIT {page_size} OFFSET {offset};"""
    cursor.execute(query)
    data = cursor.fetchall()

    df = pd.DataFrame(data, columns=["BOOKING_ID","INCOMPLETE_RIDE_REASON" ])
    st.write(f"Showing records {offset + 1} to "  f"{min(offset + page_size, total_records)} "f"of {total_records:,}"  )
    st.dataframe(df, use_container_width=True)


# ======= Close Connection ========
cursor.close()
connection.close()
print("Database connection closed.")