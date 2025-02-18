# PrivGeo: Privacy-Preserving Geofencing using Paillier Encryption
### Project Owner: 
Oliver Timothy
### Supervisor:
Dr Hai-Van Dang
### Project Vision
PrivGeo is a privacy-preserving geofencing system designed for organizations that prioritize the location privacy of their users while needing precise geofencing capabilities. PrivGeo supports circular geofences, enabling accurate boundary definitions without exposing user location data. Leveraging the Paillier encryption scheme, PrivGeo ensures full location privacy, offering a practical and real-time solution. This system is ideal for applications that demand advanced geofencing while maintaining user trust by keeping location information secure, thereby promoting the broader adoption of location-based services in privacy-sensitive contexts. 
#### How to Run:
Open Docker and VScode. In VScode open project folder then run the command "docker-compose up -d --build". Wait for it to fetch all geofences. 

#### Where to Find Tests:
Runtime and Scalability can be found in main of User.py. The Scalability test cases need to be changed mannually by changing the number of requests, same goes for Runtime test cases however to change this you need to go to Geofencing-Microservice folder and change number of geofences i have commented saying what variable you need to change in app.py.
Accuracy and Security Overhead can be found in main of CircularGeofencing.py.
