# notification-service
Local setup:
1. git clone https://github.com/swagatacha/notification-service.git
2. cd notification-service
3. open cmd 
4. Create .env file from .env-sample
5. You can modify docker-compose.yml file by removing redis, mongo  if you want to use exeisting one 
6. In docker dsktop 5 containers will be in running state (mongodb, redis, rabbitmq, notification_service, logstash) with run command: docker compose up --build -d.
7. Intially you can stop logstash container because we need to populate mongo template first. you can stop logstash container from docker desktop by clicking stop action otherwise from cmd, you can run docker stop <container_name>
8. Outside of notification-service, copy lambda folder in your machine 
    1. cd lambda
    2. activate virtual env (venv\Scripts\activate)
    3. pip install -r requirements.txt
    4. run : python -m lib.notification_template_processing
9. After successfully mongo template addition, you can restart logstash container from either docker desktop or docker restart <container_name>
10. you can open rabbitmq ui localhost:15762 to check queues inbound /outbound message processing
11. this command stop all containers and remove from docker: docker compose down
12. If you made any change in codebase, You can restart container individually by docker restart <container_name> or you can rebuild all containers in backgroup by this command: docker compose up -d 
13. In scripts folder we have 2 more files to clean up old mongo data and redis key which we will setup as crontab

Production Lambda SetUp
1. copy lambda folder in your machine 
2. cd lambda
3. pip install -r requirements.txt -t . 
4. Compress-Archive -Path * -DestinationPath lambda_deploy_package.zip
5. Create the AWS Lambda Function in AWS console : AWS Console > Lambda > Create function.
6. Upload the Code : Code > Upload from > .zip file (upload lambda_deploy_package.zip)
7. Set the Handler : Format: <filename>.<function name> (lambda_function.lambda_handler)

docker run -d --name redis-container -p 6379:6379 redis:latest

docker run -d --name rabbitmq-container -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=admin rabbitmq:3.12-management

docker run -d --name mongo-container -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password -p 27017:27017 mongo:latest


