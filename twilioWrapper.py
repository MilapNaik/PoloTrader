# we import the Twilio client from the dependency we just installed
from twilio.rest import Client

class twilio:
	def __init__(self, AccountSID, AuthToken, MyNumber, TwilioNumber):
		self.AccountSID = AccountSID
		self.AuthToken = AuthToken
		self.MyNumber = MyNumber
		self.TwilioNumber = TwilioNumber
 
	def send_sms(self, body):
		client = Client(self.AccountSID, self.AuthToken)

		# change the "from_" number to your Twilio number and the "to" number
		# to the phone number you signed up for Twilio with, or upgrade your
		# account to send SMS to any phone number
			
		client.messages.create(to=self.MyNumber, 
							   from_=self.TwilioNumber, 
							   body=body)