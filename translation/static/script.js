document.getElementById('file').addEventListener('change', function () {
    const fileNameDisplay = document.getElementById('fileName');
    const file = this.files[0];

    if (file) {
        fileNameDisplay.textContent = `✅ File Selected: ${file.name}`;
        fileNameDisplay.style.color = "#28a745";
    } else {
        fileNameDisplay.textContent = "No file chosen";
        fileNameDisplay.style.color = "#555";
    }
});

document.getElementById('uploadButton').addEventListener('click', function () {
    const fileInput = document.getElementById('file');
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file first.");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('processing').classList.remove('hidden');
    document.getElementById('result').classList.add('hidden');

    fetch('/translation/translate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('processing').classList.add('hidden');
        document.getElementById('result').classList.remove('hidden');
        document.getElementById('translatedText').textContent = data.translatedText;

        document.getElementById('downloadButton').onclick = function () {
            const formattedText = formatTextForDownload(data.translatedText, 15); // 15 words per line
            const blob = new Blob([formattedText], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'translated_output.txt';
            a.click();
            window.URL.revokeObjectURL(url);
        };
    })
    .catch(error => {
        document.getElementById('processing').classList.add('hidden');
        alert('Error during translation. Please try again.');
        console.error('Error:', error);
    });
});

// Function to format the text with proper paragraph breaks and word-wrap
function formatTextForDownload(text, wordsPerLine) {
    const paragraphs = text.trim().split(/\n+/); // Split text into paragraphs based on newlines
    const formattedParagraphs = paragraphs.map(paragraph => {
        return wrapText(paragraph, wordsPerLine); // Wrap text for each paragraph
    });
    return formattedParagraphs.join('\n\n'); // Join paragraphs with double newlines
}

// Function to wrap text by a specified number of words per line
function wrapText(paragraph, wordsPerLine) {
    const words = paragraph.split(' ');
    let wrappedText = '';
    for (let i = 0; i < words.length; i += wordsPerLine) {
        wrappedText += words.slice(i, i + wordsPerLine).join(' ') + '\n'; // Add new line after 'wordsPerLine' words
    }
    return wrappedText.trim(); // Trim any extra spaces at the end
}
