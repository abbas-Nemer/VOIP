from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import pyaudio
from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish

class Client(DatagramProtocol):
    def startProtocol(self):
        py_audio = pyaudio.PyAudio()
        self.buffer = 1024

        
        target_ip = input("Enter the provider IP address: ")
        target_port = int(input("Enter the provider port number: "))
        self.provider_address = (target_ip, target_port)

        sip_username = input("Enter your username: ")
        sip_password = input("Enter your password: ")

        self.output_stream = py_audio.open(format=pyaudio.paInt16, output=True, rate=44100, channels=2,
                                           frames_per_buffer=self.buffer)
        self.input_stream = py_audio.open(format=pyaudio.paInt16, input=True, rate=44100, channels=2,
                                          frames_per_buffer=self.buffer)

        self.xmpp_client = client.XMPPClientFactory(jid.JID(f'{sip_username}@example.com'),
                                                    sip_password)
        self.xmpp_client.addBootstrap('//event/stream/authd', self._authd)

        self.xmlstream = None

        reactor.callInThread(self.record)

    def _authd(self, xmlstream):
        self.xmlstream = xmlstream
        self.xmlstream.addObserver('/message', self.messageReceived)

    def messageReceived(self, message):
        if message.hasAttribute('data'):
            audio_data = message['data']
            self.output_stream.write(audio_data)

    def record(self):
        while True:
            data = self.input_stream.read(self.buffer)
            self.transport.write(data, self.provider_address)
            self.send_audio_data(data)
            print("Sending voice data as bytes:", data)

    def send_audio_data(self, data):
        if self.xmlstream:
            message = domish.Element(('jabber:client', 'message'))
            message['to'] = f'{sip_username}@example.com'
            message['type'] = 'chat'
            message.addElement('data', content=data)
            self.xmlstream.send(message)

    def datagramReceived(self, datagram, addr):
        self.output_stream.write(datagram)

if __name__ == '__main__':
    port = int(input("Enter the port number: "))
    print("Working on port:", port)
    reactor.listenUDP(port, Client())
    reactor.run()
