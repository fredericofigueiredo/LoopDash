import io
import base64
import uuid
import boto3
from flask import Flask, request, url_for, send_file, render_template, stream_with_context


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('upload.html')


@app.route('/upload_song', methods=['POST'])
def upload_song():

    # Get data from form
    song_file = request.files['song']
    uploader_name = request.form['uploader_name']
    song_name = request.form['name']
    bpm = request.form['bpm']
    description = request.form['description']
    genre = request.form['genre']

    # Field Validation

    # Check if any field is empty
    if not song_file or not song_name or not bpm or not description or not genre or not uploader_name:
        return "All fields are required", 400

    # Validate uploader_name
    if not isinstance(uploader_name, str):
        return "Invalid uploader name", 400

    # Validate song_name
    if not isinstance(song_name, str):
        return "Invalid song name", 400

    # Validate bpm
    try:
        bpm = int(bpm)
    except ValueError:
        return "Invalid BPM", 400

    # Validate description
    if not isinstance(description, str):
        return "Invalid description", 400

    # Validate genre
    if not isinstance(genre, str):
        return "Invalid genre", 400

    # Check file extension
    allowed_extensions = {'mp3', 'wav'}
    if song_file.filename.split('.')[-1].lower() not in allowed_extensions:
        return "Invalid file format. Only MP3 and WAV files are allowed.", 400

    # Generate song_id
    song_id = str(uuid.uuid4())

    # save song to S3
    s3 = boto3.client('s3')
    response = s3.put_object(
        Bucket='loopdash-audiofiles',
        Key=f'{song_id}.mp3',
        Body=song_file
    )

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        return "Failed to upload song to S3", 500

    # create URL using website URL and encode the song_id
    song_url = url_for(
        'download_song', song_id=song_id, _external=True)

    # save details of that song to dynamodb

    # save details of that song to dynamodb
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('audio_details')
    table.put_item(
        Item={
            'song_id': song_id,
            'song_name': song_name,
            'uploader_name': uploader_name,  # assuming uploader_name is available
            'bpm': bpm,
            'description': description,
            'genre': genre
        }
    )

    return render_template('upload_result.html', song_url=song_url)


@app.route('/play_song/<encoded_song_id>')
def play_song(encoded_song_id):

    print(encoded_song_id)
    # decode the song_id
    """decoded_song_id = base64.urlsafe_b64decode(encoded_song_id).decode()

    # get song from S3
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='your-bucket-name',
                             Key=f'{decoded_song_id}.mp3')

    # create in-memory file-like object
    song_file = io.BytesIO()
    for chunk in response['Body']:
        song_file.write(chunk)

    # send file for playing
    song_file.seek(0)
    return app.response_class(
        stream_with_context(song_file),
        mimetype='audio/mpeg',
        headers={'Content-Disposition': f'attachment; filename={decoded_song_id}.mp3'}
    )"""
    return render_template('playndownload.html', song_url=encoded_song_id)


@app.route('/download_song/<encoded_song_id>')
def download_song(encoded_song_id):
    # decode the song_id
    decoded_song_id = base64.urlsafe_b64decode(encoded_song_id).decode()

    # get song from S3
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='your-bucket-name',
                             Key=f'{decoded_song_id}.mp3')
    song_data = response['Body'].read()

    # create in-memory file-like object
    song_file = io.BytesIO(song_data)

    # send file for download
    return send_file(song_file, attachment_filename=f'{decoded_song_id}.mp3', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
