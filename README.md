#Conference Organization App 02/21/2016

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

## Design Methods 

1. Session Objects -- These are similar to Conference objects. The Session's parent is a Conference. 

1.1 duration: This a an integer property, this beneficial when comparing duration's of different Sessions and Querying 

1.2 startTime : Since the Start time will be using 24hour clock it was beneficial here to use an integer property, the allowed for easy comparisons of different session start times. Allows for less worry about am and pm, just in case there are sessions at 6am and 6pm.

1.3. Session Type -- Chose to go with an array of strings. Used ndb.StringProperty(repeated = True) for typeOfSession to allow Sessions to have multiple types, to deal with Sessions that are both lecture and workshop for example.

1.4. Speaker(String) -- Chose to go with just a String property, for simplicty, used ndb.StringProperty()for Speaker. There is also a Speaker Object which explained below. 

1.5. SessionForm -- This is used to populate the Session object, websafeConferenceKey is present in SessionForm, this allows the user to put in the Conference Key that will be the parent of that Session. 
	- Added speakersEmail Field to Sessionfrom, this allows the user to input the speakers email when creating a session then automatically add that session to the Speakers list of Sessions (sessionsToSpeak)


#Speaker Object 
These are similar to Profile Objects . The user can create a speaker object by adding the following information:

- Name : Speaker's name

- mainEmail : Speakers email address that is used to make a Speaker Key. This is the only required field because the email address is used to create the key and also is also used in the method getSessionsBySpeakerEmail this method is explained below.
    
- phone : Extra piece of information about the Speaker.

## def getSessionsBySpeakerEmail
This is an Endpoint Method that utilizes, the Speaker Object. Given the speaker email as request, it checks the speaker object for all the sessions the speaker has been signed up for, then returns the list of Sessions. 

# Speaker entity Workflow:
This more of a workflow to utilize the Speaker Object:

1. The user must first, Create a Speaker Object using endpoints method "createSpeaker"

2. Then Create a Session and add the Speakers email in the "SpeakersEmail", this automatically adds the Session to the Speakers   list "sessionsToSpeak"

3. To Verify that the sessions are being correctly added to the Speaker Object use the endpoints method "getSessionsBySpeakerEmail"

4. NOTE that "getSessionsBySpeakerEmail" is different from getSessionsBySpeaker because it rather checks the Speaker Object to see what sessions the Speaker is registered to speak in.

The Design to choice to use the email, is because the email is unique, just in case there are two speakers with the same name and to allow for future development to have email's sent to Speakers of the list of Sessions they are signed up for.




## New Queries 
1. getSessionsByStartTime : 
	Using the following Properties :
	- websafeConferenceKey
	- startTime
	The user can Query for all Sessions that occur Past a certain time, for example for all sessions after 2pm, startTime should be set to 1400.  This is the benifit of having the startTime us 24hour clock because is can easily displayed as integers between 0000-2359 . 


1. getSessionsByDuration : 
	Using the following Properties :
	- websafeConferenceKey
	- Duration
	The user can Query for all Sessions that are less than or equal to a certain duration, for example search for all Sessions that are 2 hours or less, the user will simple use the integer 2 for the duration. 


## Query Problem
- How would you handle a query for all non-workshop sessions before 7pm ?
    -The problem here that I noticed is that typeOfSession is repeated field so running a query on it for type that is non-workshop is difficult because it you must search through the array ensure that workshop is not a present type.
    - The solution I created was to use a "QuerySessionForm" that has the following inputs:
        - typeOfSession : The user Type a Session Type
        - matchSessionType : A Boolean to see if the method look for the typeOfSession added above.
        - startTime : The user inserts a Start time
        - Before_OR_After : The User either types in "Before" or "After" referring the start time they are looking for.
        - websafeConferenceKey : The WebSafe Key of the Conference they are looking for.
    - So for example to Find all the non-workshop sessions before 7pm the user would use the following:
        - typeOfSession = Workshop
        - matchSessionType = False
        - startTime = 1900
        - Before_OR_After = Before
        - websafeConferenceKey : abcdefghijklmnopqrstuvwxyzthequickbrownfoxjumpedoverthedog 



## GENERAL USAGE NOTES
-------------------

# Session methods
1.createSession(SessionForm, websafeConferenceKey) -- open only to the organizer of the conference
1. getConferenceSessions(websafeConferenceKey) -- Given a conference, return all sessions

2. getConferenceSessionsByType(websafeConferenceKey, typeOfSession) Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)

3.getSessionsBySpeaker(speaker) -- Given a speaker, return all sessions given by this particular speaker, across all conferences

# Wishlist methods
1.addSessionToWishlist(SessionKey) -- adds the session to the user's list of sessions they are interested in attending

2.You can decide if they can only add conference they have registered to attend or if the wishlist is open to all conferences.

3.getSessionsInWishlist() -- query for all the sessions in a conference that the user is interested in

4.deleteSessionInWishlist(SessionKey) -- removes the session from the user’s list of sessions they are interested in attending













