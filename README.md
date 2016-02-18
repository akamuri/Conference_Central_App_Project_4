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


<<<<<<< HEAD
[1]: https://console.developers.google.com/
[2]: https://localhost:8080/
[3]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool

## GENERAL USAGE NOTES
-------------------

# Session methods
1.createSession(SessionForm, websafeConferenceKey) -- open only to the organizer of the conference
1. getConferenceSessions(websafeConferenceKey) -- Given a conference, return all sessions
1. getConferenceSessionsByType(websafeConferenceKey, typeOfSession) Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)
1.getSessionsBySpeaker(speaker) -- Given a speaker, return all sessions given by this particular speaker, across all conferences

# Wishlist methods
1.addSessionToWishlist(SessionKey) -- adds the session to the user's list of sessions they are interested in attending

1.You can decide if they can only add conference they have registered to attend or if the wishlist is open to all conferences.

1.getSessionsInWishlist() -- query for all the sessions in a conference that the user is interested in

1.deleteSessionInWishlist(SessionKey) -- removes the session from the user’s list of sessions they are interested in attending

# New Queries 
1. getSessionsByStartTime : Query for Sessions by Start Time.

1. getSessionsByDuration : Query for Sessions by Duration 
||||||| merged common ancestors
[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool
=======
[1]: https://console.developers.google.com/
[2]: https://localhost:8080/
[3]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool

## GENERAL USAGE NOTES
-------------------

# Create a Session
>>>>>>> c91657271e63eff80fa923fcc6d9099b3fc321ab
