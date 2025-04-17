document.getElementById('file').addEventListener('change', function () {
    const fileNameDisplay = document.getElementById('fileName');
    const languageSelectionDiv = document.getElementById('languageSelection');
    const file = this.files[0];

    if (file) {
        fileNameDisplay.textContent = `✅ File Selected: ${file.name}`;
        fileNameDisplay.style.color = "#28a745";
        languageSelectionDiv.classList.remove('hidden');
        // Reset language selections when a new file is chosen
        document.getElementById('sourceLanguage').value = '';
        document.getElementById('targetLanguage').value = '';
        // Re-enable all target language options
        const targetLangSelect = document.getElementById('targetLanguage');
        const options = targetLangSelect.querySelectorAll('option');
        options.forEach(option => {
            option.disabled = false;
        });
    } else {
        fileNameDisplay.textContent = "No file chosen";
        fileNameDisplay.style.color = "#555";
        languageSelectionDiv.classList.add('hidden');
    }
});

document.getElementById('translateButton').addEventListener('click', function () {
    const fileInput = document.getElementById('file');
    const file = fileInput.files[0];
    const sourceLanguageSelect = document.getElementById('sourceLanguage');
    const targetLanguageSelect = document.getElementById('targetLanguage');
    const sourceLanguage = sourceLanguageSelect.value;
    const targetLanguage = targetLanguageSelect.value;

    if (!file) {
        alert("Please select a file first.");
        return;
    }

    if (!sourceLanguage) {
        alert("Please select the document language.");
        return;
    }

    if (!targetLanguage) {
        alert("Please select the target language for translation.");
        return;
    }

    if (sourceLanguage === targetLanguage) {
        alert("Document language and target language cannot be the same.");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_language', sourceLanguage);
    formData.append('target_language', targetLanguage);

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
        if (data.error) {
            alert(`Translation Error: ${data.error}`);
            document.getElementById('translatedText').textContent = "Translation failed.";
        } else if (data.translatedText !== undefined) {
            document.getElementById('translatedText').textContent = data.translatedText;
            document.getElementById('downloadButton').onclick = function () {
                const formattedText = formatTextForDownload(data.translatedText, 15);
                const blob = new Blob([formattedText], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'translated_output.txt';
                a.click();
                window.URL.revokeObjectURL(url);
            };
        } else {
            alert("No translated text received.");
            document.getElementById('translatedText').textContent = "No translation available.";
        }
    })
    .catch(error => {
        document.getElementById('processing').classList.add('hidden');
        alert('Error during translation request. Please try again.');
        console.error('Error:', error);
        document.getElementById('translatedText').textContent = "Translation request failed.";
    });
});

// Function to format the text with proper paragraph breaks and word-wrap
function formatTextForDownload(text, wordsPerLine) {
    const paragraphs = text.trim().split(/\n+/);
    const formattedParagraphs = paragraphs.map(paragraph => {
        return wrapText(paragraph, wordsPerLine);
    });
    return formattedParagraphs.join('\n\n');
}

// Function to wrap text by a specified number of words per line
function wrapText(paragraph, wordsPerLine) {
    const words = paragraph.split(' ');
    let wrappedText = '';
    for (let i = 0; i < words.length; i += wordsPerLine) {
        wrappedText += words.slice(i, i + wordsPerLine).join(' ') + '\n';
    }
    return wrappedText.trim();
}

document.getElementById('sourceLanguage').addEventListener('change', function() {
    const sourceLang = this.value;
    const targetLangSelect = document.getElementById('targetLanguage');
    const options = targetLangSelect.querySelectorAll('option');

    options.forEach(option => {
        option.disabled = (option.value === sourceLang && sourceLang !== '');
        if (option.value === sourceLang && sourceLang !== '') {
            if (targetLangSelect.value === sourceLang) {
                targetLangSelect.value = ''; // Reset target if it's the same as source
            }
        }
    });
});
