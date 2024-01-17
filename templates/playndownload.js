var audioPlayer = document.getElementById('audioPlayer');
var playButton = document.getElementById('playButton');
var downloadLink = document.getElementById('downloadLink');

// Fetch the song URL from the Flask backend
fetch('/get_song_url')
    .then(response => response.text())
    .then(songUrl => {
        // Set the href of the download link
        downloadLink.href = songUrl;

        // Start the playback when the play button is clicked
        playButton.addEventListener('click', function () {
            audioPlayer.src = songUrl;
            audioPlayer.play();
