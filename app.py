from flask import Flask
import uuid
from boto3 import resource
import boto3
from flask import request
from flask import url_for, send_file
import io
import base64
from flask import stream_with_context


def get_smallest_song_id():
    dynamodb = resource('dynamodb')
    table = dynamodb.Table('TBD')

    response = table.scan(
        ProjectionExpression='song_id'
    )

    used_ids = {item['song_id'] for item in response['Items']}
    next_id = 1

    while next_id in used_ids:
        next_id += 1

    print(f"The smallest unused song_id is {next_id}")


app = Flask(__name__)


@app.route('/upload_song')
def upload_song():
    song_id = get_smallest_song_id()

    # get song from request
    song_file = request.files['song']

    # upload song to s3
    s3 = boto3.client('s3')
    s3.put_object(song_file, 'TBD', f'{song_id}.mp3')

    # save details of that song to dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TBD')
    table.put_item(
        Item={
            'song_id': song_id,
            'song_name': song_file.filename
        }
    )

    # create URL using website URL and encode the song_id
    encoded_song_id = base64.urlsafe_b64encode(str(song_id).encode()).decode()
    song_url = url_for(
        'download_song', song_id=encoded_song_id, _external=True)

    return song_url


@app.route('/play_song/<encoded_song_id>')
def play_song(encoded_song_id):
    # decode the song_id
    decoded_song_id = base64.urlsafe_b64decode(encoded_song_id).decode()

    # get song from S3
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='your-bucket-name',
                             Key=f'{decoded_song_id}.mp3')

    # create in-memory file-like object
    song_file = io.BytesIO()
    for chunk in response['Body'].iter_chunks():
        song_file.write(chunk)

    # send file for playing
    song_file.seek(0)
    return app.response_class(
        stream_with_context(song_file),
        mimetype='audio/mpeg',
        headers={'Content-Disposition': f'attachment; filename={decoded_song_id}.mp3'}
    )


@app.route('/download_song/<song_id>')
def download_song(song_id):
    # decode the song_id
    decoded_song_id = base64.urlsafe_b64decode(song_id.encode()).decode()

    # get song from S3
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='your-bucket-name',
                             Key=f'{decoded_song_id}.mp3')
    song_data = response['Body'].read()

    # create in-memory file-like object
    song_file = io.BytesIO(song_data)

    # send file for download
    return send_file(song_file, attachment_filename=f'{decoded_song_id}.mp3', as_attachment=True)
