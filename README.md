#Conference Organization App 02/17/2016

##README
------
- Conference Organization App, is a Web application that helps you create and manage Cofereneces 
- Some of the main features the App allows you to use is :
	- Create Conferences 
	- Register and unregister for Conferences 
	- Query different Conferences
	- Create Sessions 
	- Add and delete sessions for a Users Wishlist
	- Query different Sessions 

----------------------------------------------------------------------------

## Setup Instructions
1. Update the value of `ancient-ceiling-119401` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
1. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][1].
1. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
1. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
1. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting
   your local server's address (by default [localhost:8080][2].)
1. Generate your client library(ies) with [the endpoints tool][3].
1. Deploy your application.


[1]: https://console.developers.google.com/
[2]: https://localhost:8080/
[3]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool

## GENERAL USAGE NOTES
-------------------

# Create a Session
