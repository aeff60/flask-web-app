# flask-web-app

To run the Flask web app in a Docker container, follow these steps:

1. Build the Docker image by running the following command in the terminal:

   ```
   docker build -t my_flask_app .
   ```

2. Once the image is built, you can run a container using the following command:

   ```
   docker run -p 5000:5000 my_flask_app
   ```

   This command maps port 5000 from the container to port 5000 on your local machine.

3. Open your web browser and navigate to `http://localhost:5000` to access the Flask web app.
