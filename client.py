from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

import requests

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientDB.sqlite3'

db = SQLAlchemy(app)

server_ip_address = '192.168.1.35'
# server_ip_address = '192.168.0.100'
server_port = '5000'

class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    ip_address = db.Column(db.String(39))
    port = db.Column(db.String(5), default='80')
    status = db.Column(db.String(7), default='unknown', nullable=False)

    def __repr__(self):
        return '<Device {}, status : {}>'.format(self.ip_address, self.status)
    
    def to_dict(self):
        device = {
            'id': self.id,
            'type': self.type,
            'ip_address': self.ip_address,
            'port': self.port,
            'status': self.status,
        }
        return device

# Delete old database
db.drop_all()

# Create new database
db.create_all()

@app.route('/test/<event>', methods=['GET'])
def authenticate_ip(event):
    current_device_IP = request.remote_addr

    # Find device with this ip in the database
    device = Device.query.filter_by(ip_address=current_device_IP).first()
    if device:
        if device.status != 'trusted' and event == 'abnormal':
            device.status = 'blocked'
            db.session.commit()
            # Make a request to the server to prodcast the ip address
            res = requests.get('http://' + server_ip_address + ':' + server_port + '/' + event + '/' + current_device_IP)
            if res.status_code == 200:
                abort(401)
            else:
                return jsonify({ 'message': "Something went wrong, try again later!!" }), 403

        elif device.status == "blocked":
            abort(401)
        else:
            return jsonify({ 'message': "Hi, you're welcome :)" })

    else:
        # Make a request to the server to check the ip address
        res = requests.get('http://' + server_ip_address + ':' + server_port + '/' + event + '/' + current_device_IP)

        if res.status_code == 200:
            response = res.json()

            # Add the device to local database
            newDevice = Device(ip_address=current_device_IP, status=response['device']['status'])
            db.session.add(newDevice)
            db.session.commit()

            # Check if the device's status is unknown and the event was abnormal
            if event == 'abnormal' and response['device']['status'] != 'trusted':
                abort(401)
            else:
                return jsonify({ 'message': "Hi, you're welcome :)" })
        else:
            print('#### Device with IP ' + current_device_IP + ' is NOT added!!!! Problem with the server!!!')

@app.route('/add/<address>/<status>', methods=['GET', 'POST'])
def add_new_device(address, status='unknown'):
    # Find device with this ip in the database
    device = Device.query.filter_by(ip_address=address).first()
    if device:
        device.status = status
        db.session.commit()

        return jsonify({ 'msg': 'Already exist in the database', 'device': device.to_dict() }), 202
    else:
        # Add new device to database
        device = Device(ip_address=address, status=status)
        db.session.add(device)
        db.session.commit()

        return jsonify({ 'device': device.to_dict()}), 201


if __name__ == '__main__':
    # app.run(debug=True)  # important to mention debug=True
    app.run(host='0.0.0.0', port=3000)
