from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import TeeShirtSize

from utils import getUserId

from settings import WEB_CLIENT_ID

from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms

from models import Session
from models import SessionForm
from models import SessionForms
from models import QuerySessionForm

from models import Speaker
from models import SpeakForm

from models import BooleanMessage
from models import ConflictException


from google.appengine.api import memcache
from google.appengine.api import taskqueue
from models import StringMessage

#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
MEMCACHE_SPEAKERS_KEY = "FEATURED_SPEAKERS"


CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)


CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)


Session_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    sessionKey=messages.StringField(1),
)


DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": ["Default", "Topic"],
}

OPERATORS = {
    'EQ': '=',
    'GT': '>',
    'GTEQ': '>=',
            'LT': '<',
            'LTEQ': '<=',
            'NE': '!='
}

FIELDS = {
    'CITY': 'city',
            'TOPIC': 'topics',
            'MONTH': 'month',
            'MAX_ATTENDEES': 'maxAttendees',
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


@endpoints.api(name='conference',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

# - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(
                        pf, field.name, getattr(
                            TeeShirtSize, getattr(
                                prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromUser(self):
        """Return user Profile from datastore, creating new one if non-existent."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key=p_key,
                displayName=user.nickname(),
                mainEmail=user.email(),
                teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile      # return Profile

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
            prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)

    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)

# - - - Speaker objects - - - - - - - - - - - - - - - - -

    def _copySpeakerToForm(self, speak):
        """Copy relevant fields from Speaker to SpeakerForm."""
        # copy relevant fields from Speaker to SpeakerForm
        spf = SpeakForm()
        spf.check_initialized()
        return spf

    def _createSpeakerObject(self, request):
        speaker_id = request.mainEmail
        sp_key = ndb.Key(Speaker, speaker_id)

        speaker = Speaker(
                key=sp_key,
                name=request.name,
                mainEmail=request.mainEmail,
                phone=request.phone,
            )
        speaker.put()

        return request

    # Create a Speaker Object 
    @endpoints.method(SpeakForm, SpeakForm, path='speaker',
                      http_method='POST', name='createSpeaker')
    def createSpeaker(self, request):
        """Create new speaker."""
        return self._createSpeakerObject(request)

    #Query for speakers of sessions via there email.
    @endpoints.method(SpeakForm, SessionForms,
                      path='getSessionsBySpeakerEmail',
                      http_method='GET', name='getSessionsBySpeakerEmail')
    def getSessionsBySpeakerEmail(self, request):
        """Return conferences created by user."""
        # make sure user is Authorized 
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        oneSpeaker = Speaker.query(Speaker.mainEmail == request.mainEmail)
        oneSpeaker = oneSpeaker.get()

        Sessions = []
        for sessKey in oneSpeaker.sessionsToSpeak:
            oneSession = ndb.Key(urlsafe=sessKey).get()
            Sessions.append(oneSession)
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# - - - Session objects - - - - - - - - - - - - - - - - -

    def _copySessionToForm(self, sess):
        """Copy relevant fields from Session to SessionForm."""
        # copy relevant fields from Session to SessionForm
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(sess, field.name):
                # convert Date to date string; just copy others
                if field.name == "date":
                    setattr(sf, field.name, str(getattr(sess, field.name)))
                else:
                    setattr(sf, field.name, getattr(sess, field.name))
        sf.check_initialized()
        return sf

# - - -Task 1 - - - - - - - - - - - - - - - - -
    def _createSessionObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException(
                "Session 'name' field required")

        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        # Check that user trying to Create the Session is the Owner of the Conference.
        if conf.organizerUserId != user_id:
            raise endpoints.BadRequestException(
                "You must be the Owner of the Conference to Create a Session")

        # copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['websafeConferenceKey']


        # convert dates from strings to Date objects;
        if data['date']:
            data['date'] = datetime.strptime(
                data['date'][:10], "%Y-%m-%d").date()

        # make Parent Key from Conference ID
        parent_key = ndb.Key(Conference, conf.key.id())

        # allocate new Session ID with Conference key as parent
        s_id = Session.allocate_ids(size=1, parent=parent_key)[0]

        # make Session key from ID
        s_key = ndb.Key(Session, s_id, parent=parent_key)
        data['key'] = s_key


        # Check to see if the Speakers email already present in Datastore, 
        # Then adds this Session key to Speakers list of Sessions to Speak at.
        if  data['speakersEmail']:
            oneSpeaker = Speaker.query(Speaker.mainEmail == data['speakersEmail'])
            oneSpeaker = oneSpeaker.get()
            oneSpeaker.sessionsToSpeak.append(s_key.urlsafe())
            oneSpeaker.put()
        del data['speakersEmail']


        Session(**data).put()

        # Check if there is a speaker, if so run the featuredspeaker task.
        if data['speaker']:
            taskqueue.add(
                params={
                    'websafeConferenceKey': request.websafeConferenceKey,
                    'speaker': data['speaker']},
                method='GET',
                url='/tasks/featuredSpeaker')
        return request

    @endpoints.method(SessionForm, SessionForm, path='session',
                      http_method='POST', name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)

    @endpoints.method(CONF_GET_REQUEST, SessionForms,
                      path='getConferenceSessions',
                      http_method='GET', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Return conferences created by user."""
        # make sure user is Authorized 
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        # make Conference key
        parent_key = ndb.Key(Conference, conf.key.id())

        # Query all the Sessions in this Conference 
        Sessions = Session.query(ancestor=parent_key)

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )

    @endpoints.method(QuerySessionForm, SessionForms,
                      path='getConferenceSessionsByType',
                      http_method='GET', name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Return conferences created by user."""
        # make sure user is Authorized 
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        # make Conference key
        parent_key = ndb.Key(Conference, conf.key.id())

        # Query all the Sessions in this Conference 
        Sessions = Session.query(ancestor=parent_key)

        Sessions = Sessions.filter(
            Session.typeOfSession == request.typeOfSession)

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )

    @endpoints.method(SessionForm, SessionForms,
                      path='getSessionsBySpeaker',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Return conferences created by user."""
        # make sure user is Authorized 
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # create query where session speaker and requested speaker match
        Sessions = Session.query(Session.speaker == request.speaker)

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )
# - - -Task 2 - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _sessionWishlist(self, request, reg=True):
        """add or delete sessions in the users Wishlist."""
        retval = None
        prof = self._getProfileFromUser()  # get user Profile

        # check if Session exists given websafeConfKey
        # get Session; check that it exists
        wsck = request.sessionKey
        sess = ndb.Key(urlsafe=wsck).get()
        if not sess:
            raise endpoints.NotFoundException(
                'No Session found with key: %s' % wsck)

        # wish
        if reg:
            # check if user already has session in WishList
            if wsck in prof.sessionWishlist:
                raise ConflictException(
                    "You already have this Session in your Wishlist")

            # Add session to User's WishList 
            prof.sessionWishlist.append(wsck)
            retval = True

        # unwish
        else:
            # check if user already has session in WishList
            if wsck in prof.sessionWishlist:
                # Remove session from Wishlist
                prof.sessionWishlist.remove(wsck)
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        return BooleanMessage(data=retval)

    @endpoints.method(Session_GET_REQUEST, BooleanMessage,
                      path='session/{sessionKey}',
                      http_method='POST', name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """Register user for selected conference."""
        return self._sessionWishlist(request)

    @endpoints.method(Session_GET_REQUEST, BooleanMessage,
                      path='session/{sessionKey}',
                      http_method='DELETE', name='deleteSessionInWishlist')
    def deleteSessionInWishlist(self, request):
        """unRegister user for selected conference."""
        return self._sessionWishlist(request, reg=False)

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='getSessionsInWishlist',
                      http_method='GET', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """Return conferences created by user."""
        # make sure user is Authorized 
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        prof = self._getProfileFromUser()
        wishlist = prof.sessionWishlist
        Sessions = []

        for sessKey in wishlist:
            oneSession = ndb.Key(urlsafe=sessKey).get()
            Sessions.append(oneSession)

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )

# - - -Task 3 - - - - - - - - - - - - - - - - -
# 1st new Query, search for Sessions that start past a certain time
    @endpoints.method(SessionForm, SessionForms,
                      path='getSessionsByStartTime',
                      http_method='GET', name='getSessionsByStartTime')
    def getSessionsByStartTime(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # create query where session speaker and requested speaker match
        Sessions = Session.query(Session.startTime >= request.startTime)
        Sessions = Sessions.order(Session.startTime)

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )

# 2nd new Query, search for Sessions that less that a certain duration
    @endpoints.method(SessionForm, SessionForms,
                      path='getSessionsByDuration',
                      http_method='GET', name='getSessionsByDuration')
    def getSessionsByDuration(self, request):
        """Return conferences created by user."""
        # make sure user is Authorized
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # create query where session speaker and requested speaker match

        Sessions = Session.query(Session.duration <= request.duration and Session.duration>=0)

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )
# Query Problem : Quest all non-workshop sessions before 7pm 
# Quick a dity method, in this case the user would put Workshop as SessionType and 7pm
# as start time. 
    @endpoints.method(QuerySessionForm, SessionForms,
                      path='getQueryProblem',
                      http_method='GET', name='getQueryProblem')
    def getQueryProblem(self, request):
        # make sure user is Authorized
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # create query all non-workshop sessions before 7pm
        # User would set Equal_to_Type = False, meaning they don't want that type 
        # User would set Before_OR_After = Before(string), and set the starttime to 7pm. 
        if request.Before_OR_After == "Before" :
            Sessions = Session.query(Session.startTime <= request.startTime)
            Sessions = Sessions.order(Session.startTime)
            temp = []
            for sess in Sessions:
                if request.typeOfSession in sess.typeOfSession and request.matchSessionType:
                    temp.append(sess)
                elif request.typeOfSession not in sess.typeOfSession and not request.matchSessionType:
                    temp.append(sess)
            Sessions = temp
        else:
            Sessions = Session.query(Session.startTime >= request.startTime)
            Sessions = Sessions.order(Session.startTime)
            temp = []
            for sess in Sessions:
                if request.typeOfSession in sess.typeOfSession and request.matchSessionType:
                    temp.append(sess)
                elif request.typeOfSession not in sess.typeOfSession and not request.matchSessionType:
                    temp.append(sess)
            Sessions = temp

        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in Sessions]
        )


# - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf

    def _createConferenceObject(self, request):
        """Create or update Conference object, returning ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException(
                "Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound
        # Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on
        # start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(
                data['startDate'][:10], "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(
                data['endDate'][:10], "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        # both for data model & outbound Message
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
            setattr(request, "seatsAvailable", data["maxAttendees"])

        # make Profile Key from user ID
        p_key = ndb.Key(Profile, user_id)
        # allocate new Conference ID with Profile key as parent
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        # make Conference key from ID
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference & return (modified) ConferenceForm
        Conference(**data).put()

        # TODO 2: add confirmation email sending task to queue
        # Look for TODO 2
        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(params={'email': user.email(),
                              'conferenceInfo': repr(request)},
                      url='/tasks/send_confirmation_email'
                      )

        return request

    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
                      http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)

    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    # Query Confrences Methods
    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='queryConferences',
                      http_method='POST', name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "")
                   for conf in conferences]
        )

    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='getConferencesCreated',
                      http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # make profile key
        p_key = ndb.Key(Profile, getUserId(user))
        # create ancestor query for this user
        conferences = Conference.query(ancestor=p_key)
        # get the user profile and display name
        prof = p_key.get()
        displayName = getattr(prof, 'displayName')
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[
                self._copyConferenceToForm(
                    conf,
                    displayName) for conf in conferences])

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='filterPlayground',
                      http_method='POST', name='filterPlayground')
    def filterPlayground(self, request):
        q = Conference.query()

        # TODO
        # add 2 filters:
        # 1: city equals to London
        q = q.filter(Conference.city == "London")

        # 2: topic equals "Medical Innovations"
        q = q.filter(Conference.topics == "Medical Innovations")

        # 3: order by conference  name
        q = q.order(Conference.name)

        # first for month of June
        q = q.filter(Conference.maxAttendees > 10)

        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in q]
        )

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(
                filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)
        return q

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name)
                     for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous filters
                # disallow the filter if inequality was performed on a different field before
                # track the field on which the inequality operation is
                # performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)

# - - - Registration - - - - - - - - - - - - - - - - - - - -
    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser()  # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """unRegister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending',
                      http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        # TODO:
        # step 1: get user profile
        prof = self._getProfileFromUser()  # get user Profile

        # step 2: get conferenceKeysToAttend from profile.
        # to make a ndb key from websafe key you can use:
        # ndb.Key(urlsafe=my_websafe_key_string)
        array_of_keys = [ndb.Key(urlsafe=wsck)
                         for wsck in prof.conferenceKeysToAttend]

        # step 3: fetch conferences from datastore.
        # Use get_multi(array_of_keys) to fetch all keys at once.
        # Do not fetch them one by one!
        conferences = ndb.get_multi(array_of_keys)

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, "")
                                      for conf in conferences]
                               )
# - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)).fetch(projection=[Conference.name])

        if confs:
            print "We are going to set the announcement"
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:',
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
            print "The announcement has been created. Here: ", announcement
        else:
            print "We are going to delete the announcement from memcache"
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)
            print "The announcement has been deleted from memcache"

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/announcement/get',
                      http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        # TODO 1
        # return an existing announcement from Memcache or an empty string.
        announcement = memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY)
        if not announcement:
            announcement = ""
        return StringMessage(data=announcement)

    @staticmethod
    def _cacheFeaturedSpeaker(websafeConferenceKey, speaker):
        """Create Announcement & assign to memcache; used by
        memcache getFeaturedSpeaker().
        """

        conf = ndb.Key(urlsafe=websafeConferenceKey).get()
        p_key = ndb.Key(Conference, conf.key.id())

        featuredSessions = Session.query(ancestor=p_key)
        featuredSessions = featuredSessions.filter(Session.speaker == speaker)

        if featuredSessions.count() > 1:
            announcement = 'The featured speaker will be : %s. For the following sessions %s' %\
                (speaker, ', '.join(sess.name for sess in featuredSessions))
            #print announcement
            memcache.set(MEMCACHE_SPEAKERS_KEY, announcement)
        else:
            announcement = ""
            memcache.delete(MEMCACHE_SPEAKERS_KEY)

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='session/announcement/get',
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Return Announcement from memcache."""
        announcement = memcache.get(MEMCACHE_SPEAKERS_KEY)
        if not announcement:
            announcement = ""
        return StringMessage(data=announcement)


# registers API
api = endpoints.api_server([ConferenceApi])
