# Surveillor
Monitor the environs of the house with multiple cameras and Raspberry Pi, Python, MQTT and Node-Red.

## Background
I have built a DIY Home Automation system as an Internet of Things (IoT). The beating heart of this system is a messaging hub that enables networking nodes wirelessly in the pub-sub model. The hub organizes information by topics and any node can subscribe to a topic to publish a message any time or be instantly notified when a new message appears. Nodes send payloads bearing sensor data to trigger action or raise alarms upon detection of unusual events or activities.

The surveillance system is a subsystem within this system. It has surveillance units, each of which is an older-model Raspberry Pi equipped with pi camera. The unit surveils a zone around the house continuously, looking for motion or presence, and sending footage to the hub at a regular frequency. At the hub, payloads are ingested, processed and presented as surveillance footage in a dashboard on a web-site. 

Here is a look at the web-site:
<img width="1440" alt="HomeAutomation_Dash" src="https://user-images.githubusercontent.com/5471571/149216914-5dfda87c-0dc0-4054-a960-321b07ae4fb7.png">

## IoT Stack

I have used an IoT Stack with the following software, each running as a service in a docker container on the hub.
1. **Mosquitto MQTT** for networking nodes with the hub in a pub-sub model. The hub hosts an MQTT broker. Each node has an MQTT client installed. MQTT is a protocol for wireless communications over WiFi. 
2. **Node-RED** for ETL'ing. ETL stands for data operations *extract, transform and load*. Node-RED is often described as a "low code" programming tool where the developer builds an app from code blocks that are organized in various drawers according to function. The developer drags and drops the code blocks on to a coding canvas and then wires them together to create a flow. A message payloads flows through the wire and is updated with processing at each code block. This makes flow of information transparent and programs are easy to create. And although Node-Red is described as "low code", it runs Node.js under the hood, making the powerful features of this javascript-based programming language available to the programmer.
3. **InfluxDB** as a database for *telemetry*. Sensor data is time-series and InfluxDB is a relational database adapted to suit handling time-series data.
4. **Grafana** as the presentation layer.

Of these, 1 and 2 are relevant to the Surveillance sub-system. I have found use for 3 and 4 in my automated hydroponic growout sub-system and I have opted not to use them for the surveillance sub-system. Each software runs as a service in a docker container. This is important because it means I do not need to back up the software, only the application data which has a much smaller footprint. In the eventuality that restoring software becomes necessary, it is a simple step of pulling docker images from a repository and spinning up containers, followed by restoring application data from backups. This takes only a few minutes and is dependable, as opposed to reinstalling software which is time-consuming and often throws up surprises. 

## Results

And here is a look at some of the "intrusions" that the surveillance system caught, including a very cute offender :)

1 | 2 | 3 
--| --| --
![Cutie pie](https://user-images.githubusercontent.com/5471571/149209114-507098d3-0338-4a5a-97da-b2640acf808e.JPG) | ![Hand partial](https://user-images.githubusercontent.com/5471571/149209120-e4913357-4463-4435-b871-49fbcd6c347a.JPG) | ![Hand blocking](https://user-images.githubusercontent.com/5471571/149209128-e59d0ded-e86f-41ed-92f8-b0e7a9b54a95.JPG)
![Dim figure](https://user-images.githubusercontent.com/5471571/149209134-7176ec37-6c24-4af2-b8f7-75ccb7ac9183.JPG) | ![Full frontal](https://user-images.githubusercontent.com/5471571/149209147-fdd64b67-2f95-4cc8-81d8-cf8de9600e8a.JPG) | ![Arm only](https://user-images.githubusercontent.com/5471571/149209152-045d79bd-3bc1-448a-ab2f-65d5bbb64692.JPG) 
![Shadowy partial figure](https://user-images.githubusercontent.com/5471571/149209157-152fe3a6-b818-4a45-ab0f-1a18ba1ab081.JPG) | ![Backlit figure](https://user-images.githubusercontent.com/5471571/149209168-331f4058-3b94-42ff-9f63-26831f23a469.JPG) | ![Obstructed view](https://user-images.githubusercontent.com/5471571/149209128-e59d0ded-e86f-41ed-92f8-b0e7a9b54a95.JPG)

You can see that the system detects presence even in sub-optimal conditions. I have programmed it to send me a message via Telegram app when this happens. 

## Python Classes

There are two steps to detecting presence, first being detection of motion and second being detection of objects. If the object is a person, then it is called out as presence. I have written modules for motion and object detection as follows:
1. **MotionDetector.py**: I have implemented a robust algorithm to detect motion and filter out effects of varying light conditions or camera shake. 
2. **ObjectDetector.py**: I have implemented deep learning using the Tensorflow framework and the Mobilenet Convolutional Neural Network. The classifier here works with an RGB image object. 
3. **classifiers.py**: I have implemented a common interface to make available multiple deep-learning models to use in object detection. I have programmed two classes to this interface for use in the app and the selection can be expanded at a later time. The implementation loosely follows the *Object Factory* pattern. An object of the class **classifiers** expects an input image as an object of the class **classifyable**.
4. **classifyable.py**: Following the *Object Factory* pattern for this computer vision application, I have implemented this class for feeding imaging input to the algorithm. In different parts of the application, an image is required in a form suitable to the context. This class enables straddling the different forms such an RGB image, a mathematical array or encoded text.

To understand the implementation, you can refer to the Jupyter notebooks.
- **motion.ipynb** describes the steps in the algorithm for motion detection. The class **MotionDetector.py** implements the algorithm for use in the app and the usage is documented in **DemoMotionDetector.ipynb**.
- **Surveil.ipynb** describes the steps in object detection with deep-learning using the Mobilenet Convolutional Neural Network (CNN). The class **ObjectDetector.py** implements the computer vision algorithm. There is a variety of CNNs in the TensorFlow framework to choose from **Surveil2.ipynb** looks at an alternative, Coco SSD. The notebook calls out what is different about usage of this model with implications for the codebase. The module **classifiers.py** then implements a common interface and implements two classes to this interface, making available both models. 

## Deployment

I have dockerized the app for deployment to a surveillance node as follows:
1. Create an image with Dockerfile, starting with base image that has Python 3.7 for Buster and adding other packages for Python.
2. Create a container using docker-compose YAML, using the image from 1. and provisioning resources including environment variables, shared storage and host devices. 

Accessing the pi camera from inside a docker container requires some set up on the host to modify permissions and some resource-sharing via YAML.

## Lessons Learned

My wife and I bounght a lawn mower. On the very first day, after unboxing and fueling it, it would not start. My neighbors Jim and Barbara happened to be out on their evening walk and saw us struggle. Jim offered to take a look and within minutes, he had the machine running as if by magic.

I thought Jim must be an engineer and I asked him whether he had experience working with machinery. Turned out he had no engineering background. His secret was, "You just look for what you can fiddle with, play around and observe what it does and figure it out." With this attitude, Jim had figured out easily what I, with a Ph.D. in mechanical engineering, had struggled with.

**WHAT A WONDERFULLY EMPOWERING ATTITUDE!**

I took this lesson to heart and am regulalry in my workshop making projects, incorporating new technologies and learning about them. It may be easier to just buy an off-the-shelf solution for many problems I have tackled, but making on my own is a learning experience like no other. And being in the tech field, I find I learn valuable lessons for making good decisions about the technologies we use in my field. 

Often, what appears easy at the start of a project turns out to be difficult, and what appears difficult turns out to be easier than imagined. **These surprises are where learning happens.** For example, I thought that running deep-learning for computer vision on an old Raspberry Pi, a credit-card sized computer with less computation horsepower than a desktop PC, would be dauting. It turned out to be among the easier challenges with sufficient material available on the web to guide the process. On the other hand, deploying the application, once ready, using docker appeared easy, but prosed many unforseen challenges for the Raspberry Pi. Here are some lessons learned:

1. I wanted to deploy the app as a docker container. Docker is the current standard for how apps for web and mobile are deployed, at least in the linux world. Once an app is dockerized, deploying anywhere is as simple as pulling the docker image from a repository with `docker pull` and spinning up a container with `docker run`. In two commands on the terminal prompt, the app is deployed. To create an image, I needed a base image as the starting point and this proved to be the first challenging task. Many images proved unsuitable for the ARM architecture of the Raspberry Pi's microprocessor. Even when a base image was compatible with the Pi's ARMv7, it would then reject the Python libraries for scientific computation that I needed for my app. The process of creating image from Dockerfile containing the requirements manifest would stall or throw incomprehensible errors arising out of incompatibilities buried deep in the dependency tree. What worked was an interative process of experimentation. 
- To start with, I found a suitable base image by trial-end-error and with a little help from stackoverflow.com. 
- Several iterations followed in which I experimented with installing one library at a time via requirements manifest, winnowing down the list to those that could be successfully installed in this manner, updating the dockerfile at the end.
- In subsequent iterations, I tried installing the remaining libraries manually by launching an interactive shell with the docker container and debugging installation process from within. With successul installation in this way, I had more options - to create an intermediate image from the running container instance using `docker commit` or updating the dockerfile and including `pip install` commands. I tried both and found the latter approach simpler and opted for that.
- Success! I now had all pre-requisite libraries installed, some via the requirements manifest, others via Python's 'pip' installer and one from the downloaded 'whl' file in the app folder. What remained was to add the entry-point to the dockerfile to start the app everytime the container was spun up.
2. Having deployed the app, I found it would run for a while and then freeze. Curious, I looked up the resources used by the app and found that while the memory usage was a reasonable 5% - 6%, CPU usage was nearly 90%. My app was taking up almost all of the CPU's computing power. in hindsight, this wasn't surprising since the app has a 'forever-while loop' where it takes snaps, detects motion, detects presence, packs the annotated image in a payload and ships it to the Home Automation hub. This cycle of events happens over and over and naturally took up (nearly) all available computing cycles. The solution was to put a small delay in the while loop, even as little as 1 second. This small change brough the CPU usage to under 50% from near 90%.
3. The MQTT connection between client and broker must be stable over weeks and months. Initially, I observed issues with the stability of the connection. The connection would break and not resume even though I had programmed it to reconnect upon disconnecting. Fixing this issue required diving deeper into the mechanics of MQTT and understanding details such as:
- The difference between a persistent connection and non-persistent connection.
- The effect of paramters such as Quality of Service (QoS) and retention policies on client and broker.
- The event loop and how callbacks were handled.
With this research and conclusions from designed experiments, I found the only way to have a stable connection was as follows:
- Connect in non-persistent manner, connecting at the start of each iteration of the forever-while loop and disconnected towards the end after shipping payload.
- Start the event-loop after making a connection and stop it just before disconnecting. Do not include code to connect upon disconnecting as the loop takes care of that when the need arises.
- Put the code for making connection, registering callbacks to events and starting the event-loop in a try-catch block so the program can continue in case any of those steps fails for transient reasons.
With these changes, I now have a dependable connection.





