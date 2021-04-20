from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

import requests

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientDB.sqlite3'

db = SQLAlchemy(app)

server_ip_address = '192.168.0.100'
# server_ip_address = '192.168.1.36'
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
            'event': self.status,
        }
        return device


@app.route('/test/<event>', methods=['GET'])
def authenticate_ip(event):
    current_device_IP = request.remote_addr

    # Find device with this ip in the database
    device = Device.query.filter_by(ip_address=current_device_IP).first()
    if device:
        if device.status == "blocked":
            abort(401)
        else:
            return jsonify({ 'message': "Hi, you're welcome :)" })

    else:
        # Make a request to the server to check the ip address
        res = requests.get('http://' + server_ip_address + ':' + server_port + '/' + current_device_IP + '/' + event)

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
            print('!!!! Request to the server failed !!!!!')

@app.route('/add/<address>/<status>', methods=['GET', 'POST'])
def add_new_device(address, status='unknown'):
    # Find device with this ip in the database
    device = Device.query.filter_by(ip_address=address).first()
    if device:
        return jsonify({ 'msg': 'Already exist in the database', 'device': device.to_dict() }), 303

    # Add new device to database
    newDevice = Device(ip_address=address, status=status)
    db.session.add(newDevice)
    db.session.commit()

    return jsonify({ 'device': newDevice.to_dict()}), 201


if __name__ == '__main__':
    # app.run(debug=True)  # important to mention debug=True
    app.run(host='0.0.0.0', port=80)
