create database OlaRideInsight;

use OlaRideInsight; 

CREATE TABLE ola_bookings (
    Date DATETIME,
    Time VARCHAR(20),
    Booking_ID VARCHAR(50) PRIMARY KEY,
    Booking_Status VARCHAR(100),
    Customer_ID VARCHAR(50),
    Vehicle_Type VARCHAR(50),
    Pickup_Location VARCHAR(255),
    Drop_Location VARCHAR(255),
    V_TAT DECIMAL(10,2),
    C_TAT DECIMAL(10,2),
    Canceled_Rides_by_Customer VARCHAR(255),
    Canceled_Rides_by_Driver VARCHAR(255),
    Incomplete_Rides VARCHAR(50),
    Incomplete_Rides_Reason VARCHAR(255),
    Booking_Value INT,
    Payment_Method VARCHAR(50),
    Ride_Distance INT,
    Driver_Ratings DECIMAL(3,2),
    Customer_Rating DECIMAL(3,2),
    Vehicle_Images TEXT
);

DESCRIBE ola_bookings;
select * from  ola_bookings;

# 1. Retrieve all successful bookings:
SELECT * FROM ola_bookings WHERE Booking_Status = 'Success';

# 2. Find the average ride distance for each vehicle type:
SELECT Vehicle_Type, ROUND(AVG(Ride_Distance), 2) AS Avg_Distance
FROM ola_bookings
GROUP BY Vehicle_Type
ORDER BY Vehicle_Type ASC;

# 3. Get the total number of cancelled rides by customers:
SELECT COUNT(*) AS Customer_Cancellations
FROM ola_bookings
WHERE Booking_Status='Canceled by Customer';

# 4. List the top 5 customers who booked the highest number of rides:
SELECT Customer_ID, count(*) as No_of_Rides
FROM ola_bookings
GROUP BY Customer_ID
ORDER BY No_of_Rides DESC
LIMIT 5;

# 5. Get the number of rides cancelled by drivers due to personal and car-related issues:
SELECT COUNT(*) AS Customer_Cancellations
FROM ola_bookings
WHERE Booking_Status='Canceled by Driver'  AND Canceled_Rides_by_Driver ='Personal & Car related issue';

# 6. Find the maximum and minimum driver ratings for Prime Sedan bookings:
SELECT Vehicle_Type,MAX(Driver_Ratings) AS MAXIMUM_RATING ,MIN(Driver_Ratings) AS MINIMUM_RATING
FROM ola_bookings
WHERE Vehicle_Type ='Prime Sedan';

# 7. Retrieve all rides where payment was made using UPI:
SELECT Booking_ID,Customer_ID,Vehicle_Type,Pickup_Location,Drop_Location,Booking_Value,Ride_Distance FROM ola_bookings
WHERE Payment_Method ='UPI';

# 8.  Find the average customer rating per vehicle type:
SELECT Vehicle_Type, ROUND(AVG(Customer_Rating),2) AS AVG_CUSTOMER_RATING
FROM ola_bookings
GROUP BY Vehicle_Type
ORDER BY Vehicle_Type;

# 9. Calculate the total booking value of rides completed successfully:
SELECT SUM(Booking_Value) AS TOTAL_BOOKING_VALUE 
FROM ola_bookings
WHERE Booking_Status ='Success' ;

# 10. List all incomplete rides along with the reason
SELECT Booking_ID,Incomplete_Rides_Reason
FROM ola_bookings
WHERE Incomplete_Rides ='Yes'
