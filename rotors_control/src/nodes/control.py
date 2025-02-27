#! /usr/bin/env python3
import rospy
import time
from pid import *
import message_filters
from drone.msg import rotor_speed
from rospy.topics import Publisher
from sensor_msgs.msg import NavSatFix #it basically publishes the altitude for the current scenario
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3Stamped
from geometry_msgs.msg import Vector3
from tf.transformations import euler_from_quaternion, quaternion_from_euler
from std_msgs.msg import Float64, Float64MultiArray
from gazebo_msgs.msg import ModelStates
from mav_msgs.msg import Actuators  


# Initilization of all Parameters
altitude = 0.30999
thrust = 0
vel_x = 0 
vel_y = 0 
vel_z = 0
roll = 0
pitch = 0
yaw = 0
x = 0
y = 0
z  = 0

# Giving default PID values incase no input from user
kp = 20
ki = 0.001
kd = 35
kp_roll = 0.2
ki_roll = 0.00001
kd_roll = 0.5
kp_pitch = 0.15
ki_pitch = 0.00001
kd_pitch = 0.1
kp_yaw = 50
ki_yaw = 0.01
kd_yaw = 5
kp_x = 0.13
ki_x = 0.00001
kd_x =  0.003 #0.00015
kp_y = 0.13
ki_y = 0
kd_y = 0.00015
kp_vel_x = 0.1
ki_vel_x = 0
kd_vel_x = 0.071
kp_vel_y = 0.01
ki_vel_y = 0.0
kd_vel_y = 0.0071
# Flag for checking for the first time the script is run
flag = 0
# Message to publish final motor speeds to propellers
message_pub = rospy.Publisher("/firefly/command/motor_speed", Actuators, queue_size=1000)

# Ask the user for the required target coordinates the drone should hover at
target_x,target_y,req_alt = map(float,input("Enter X,Y,Z coordinates of target : ").split())


# Gets altitude PID published to node
def setPID_alt(msg):
    global kp,ki,kd
    kp = msg.data[0]
    ki =  msg.data[1]
    kd = msg.data[2]


# Gets roll PID published to node
def setPID_roll(msg):
    global kp_roll,ki_roll,kd_roll
    kp_roll = msg.data[0]
    ki_roll =  msg.data[1]
    kd_roll = msg.data[2]


# Gets pitch PID published to node
def setPID_pitch(msg):
    global kp_pitch,ki_pitch,kd_pitch
    kp_pitch = msg.data[0]
    ki_pitch =  msg.data[1]
    kd_pitch = msg.data[2]


# Gets yaw PID published to node
def setPID_yaw(msg):
    global kp_yaw,ki_yaw,kd_yaw
    kp_yaw = msg.data[0]
    ki_yaw =  msg.data[1]
    kd_yaw = msg.data[2]

# Gets x PID published to node
def setPID_x(msg):
    global kp_x,ki_x,kd_x
    kp_x = msg.data[0]
    ki_x = msg.data[1]
    kd_x = msg.data[2]

# Gets y PID published to node   
def setPID_y(msg):
    global kp_y,ki_y,kd_y
    kp_y = msg.data[0]
    ki_y = msg.data[1]
    kd_y = msg.data[2]


# Gets current altitude  of drone from gps sensor
def calAltitude(msg):
    global altitude
    altitude  = msg.altitude
    rospy.loginfo("\nAltitude = " + str(altitude))


# Gets current velocity  of drone from gps_vel sensor
def calVelocity(msg):
    global vel_x, vel_y, vel_z
    vel_x = msg.vector.x
    vel_y = msg.vector.y
    vel_z = msg.vector.z


# Gets current roll. pitch, yaw of drone from IMU sensor
def calImu(msg):
    orinetation_list = [msg.orientation.x,msg.orientation.y,msg.orientation.z,msg.orientation.w]
    global roll, pitch, yaw 
    (roll,pitch,yaw) = euler_from_quaternion(orinetation_list)
    roll = roll * (180/3.14159265)
    pitch = pitch * (180/3.14159265)
    yaw = yaw * (180/3.14159265)

# Gets current roll, pitch, yaw of the drone from the odometry
# def calOdo(msg):
#     orinetation_list = [msg.x, msg.y, msg.z, msg.w]
#     global roll, pitch, yaw 
#     (roll,pitch,yaw) = euler_from_quaternion(orinetation_list)
#     roll = roll * (180/3.14159265)
#     pitch = pitch * (180/3.14159265)
#     yaw = yaw * (180/3.14159265)

#Gets current x,y posiiton of drone
def calPosition(pos):
    global x,y
    x = round(pos.pose[1].position.x,3)
    y = round(pos.pose[1].position.y,3)

# Gets vel_x and vel_y PID published to node
def setPID_vel_x(msg):
    global kp_vel_x,ki_vel_x,kd_vel_x
    kp_vel_x = msg.data[0]
    ki_vel_x = msg.data[1]
    kd_vel_x = msg.data[2]

def setPID_vel_y(msg):
    global kp_vel_y,ki_vel_y,kd_vel_y
    kp_vel_y = msg.data[0]
    ki_vel_y = msg.data[1]
    kd_vel_y = msg.data[2]


def alt_control(gps, vel, imu, odo):
    # Set all variables to global so as to keep them updated values
    global altitude,req_alt,flag, kp,ki,kd,roll, pitch, yaw,target_x,target_y

    # Gets drones current velocity
    calVelocity(vel)
    # Gets drones current rpy
    calImu(imu)
    # Gets drones current altitude
    calAltitude(gps)
    # Gets drones roll pitch yaw
    # calOdo(odo)
    #Gets drones current x and y position so that we can know the difference between it and the target value
    rospy.Subscriber("/gazebo/model_states",ModelStates,calPosition )

    # Subsribe to all required topics to get PID for all controllers
    rospy.Subscriber("alt_pid", Float64MultiArray, setPID_alt) 
    rospy.Subscriber("roll_pid", Float64MultiArray, setPID_roll) 
    rospy.Subscriber("pitch_pid", Float64MultiArray, setPID_pitch) 
    rospy.Subscriber("yaw_pid", Float64MultiArray, setPID_yaw) 
    rospy.Subscriber("x_pid", Float64MultiArray, setPID_x) 
    rospy.Subscriber("y_pid", Float64MultiArray, setPID_y) 
    rospy.Subscriber("vel_x_pid", Float64MultiArray, setPID_vel_x) 
    rospy.Subscriber("vel_y_pid", Float64MultiArray, setPID_vel_y) 

    # Combine the PID values into tuples so as to easily send easily to PID function
    k_alt = (kp,ki,kd)
    k_roll = (kp_roll,ki_roll,kd_roll)
    k_pitch = (kp_pitch,ki_pitch,kd_pitch)
    k_yaw = (kp_yaw,ki_yaw,kd_yaw)
    k_x = (kp_x,ki_x,kd_x)
    k_y = (kp_y,ki_y,kd_y)
    velocity = (vel_x, vel_y, vel_z)
    k_vel = (kp_vel_x,ki_vel_x,kd_vel_x,kp_vel_y,ki_vel_y,kd_vel_y)
    target = (target_x,target_y,req_alt)

    # Logging for debugging purposes
    print("\nAltitude = " + str(altitude))
    # print("Required alt = ",req_alt)
    print("Roll =", roll)
    print("Pitch =", pitch)
    print("Yaw =", yaw)
    print("X = ",x)
    print("Y = ",y)
    
    #the goal is to get a function that stabilises the r p y x and y of the drone as per the given target while maintaining altitude
    #speed returned is the final motor speed after going through the motor mixing algorithm for all controllers
    speed_publisher = PID_alt(roll, pitch, yaw,x,y, target, altitude, k_alt, k_roll, k_pitch, k_yaw, k_x, k_y, velocity, k_vel, flag)
    flag += 1 #Indicates completion of 1st run of function

    # Publish the final motor speeds to the propellers
    message_pub.publish(speed_publisher)


def control():
    # define global values for required parameters to avoid resetting to 0
    global altitude, thrust, speed

    # initialize node
    rospy.init_node("altitude", anonymous = False)  

    # Creating subscribers to get all relevant sensor data
    gps_sub = message_filters.Subscriber("/firefly/gps", NavSatFix)
    vel_sub = message_filters.Subscriber("/firefly/gps_velocity", Vector3Stamped)
    imu_sub = message_filters.Subscriber("/firefly/imu/data", Imu)
    ts = message_filters.TimeSynchronizer([gps_sub, vel_sub, imu_sub], 2)
    #one of these publishers is slower than the others
    #which is why the messages are loading relatively slowly
    ts.registerCallback(alt_control)
    rospy.spin()
# Main function
if __name__=='__main__':
    try:
        control()
    except rospy.ROSInterruptException:
        pass
        


