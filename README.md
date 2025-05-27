## Description
rs_manager is a tool built to manage a botnet without using a database or any persistent data. In time clients will be able to reconnect automatically upon server restart (for now it freezes).

rs_manager uses core features but can handle modules. Those cannot be installed via update on the client for now. You can add your custom modules quite easily by adding the corresponding methods and messages to your custom server and client.

## Important
rs_manager is not made to be easy to modify or expand. It was built as a side project and as such requires you to dive into the code to change default ips for instance. 
