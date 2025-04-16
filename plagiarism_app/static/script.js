const socket = io('/plagiarism');
let downloadResultsText = ""; // Global variable to store results

function updateFileName() {
    const fileInput = document.getElementById('zip-file');
    const fileNameDisplay = document.getElementById('selected-file-name');
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = `Selected file: ${fileInput.files[0].name}`;
    } else {
        fileNameDisplay.textContent = 'No file selected';
    }
}

function clearPreviousResults() {
    let resultsDiv = document.getElementById("results");
    let plagiarismDetectedDiv = document.getElementById("plagiarism-detected");
    let noPlagiarismDiv = document.getElementById("no-plagiarism");
    let processingDiv = document.getElementById("processing");
    let processingStatus = document.getElementById("processing-status");
    let downloadResultsBtn = document.getElementById("download-results-btn");

    plagiarismDetectedDiv.innerHTML = "";
    noPlagiarismDiv.innerHTML = "";
    resultsDiv.classList.add("hidden");
    downloadResultsBtn.classList.add("hidden");

    processingDiv.classList.add("hidden");
    processingStatus.textContent = '';
    downloadResultsText = ""; // Clear previous download text
}

document.getElementById("upload-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    clearPreviousResults();

    let formData = new FormData();
    let fileInput = document.getElementById("zip-file");

    if (fileInput.files.length === 0) {
        alert("Please select a ZIP file to upload.");
        document.getElementById('processing').classList.add('hidden'); // Ensure spinner is hidden
        return;
    }

    formData.append("file", fileInput.files[0]);

    let processingDiv = document.getElementById("processing");
    let resultsDiv = document.getElementById("results");
    let fileCountDiv = document.getElementById("file-count");
    let processingStatus = document.getElementById("processing-status");

    processingDiv.classList.remove("hidden");
    resultsDiv.classList.add("hidden");
    fileCountDiv.classList.add("hidden");
    processingStatus.textContent = 'Initializing...';

    try {
        let response = await fetch("/plagiarism/upload", {
            method: "POST",
            body: formData
        });

        let data = await response.json();

        if (data.error) {
            alert(data.error);
            processingDiv.classList.add("hidden");
            return;
        }

        let totalFiles = data.num_files;
        fileCountDiv.innerHTML = `Total files to process: ${totalFiles}`;
        fileCountDiv.classList.remove("hidden");
        processingStatus.textContent = 'Starting processing...';

        socket.emit('process_files', {});

    } catch (error) {
        console.error("Error during file upload:", error);
        alert("An error occurred during file upload.");
        document.getElementById('processing').classList.add('hidden');
    }
});

socket.on('progress_update', function(data) {
    const progress = Math.round(data.progress);
    document.getElementById("processing-status").textContent = `${data.current_file} (${progress}%)...`;
});

socket.on('processing_complete', function(data) {
    console.log("Processing Complete Data:", data); // For debugging

    let resultsDiv = document.getElementById("results");
    let plagiarismDetectedDiv = document.getElementById("plagiarism-detected");
    let noPlagiarismDiv = document.getElementById("no-plagiarism");
    let processingDiv = document.getElementById("processing");
    let processingStatus = document.getElementById("processing-status");
    let downloadResultsBtn = document.getElementById("download-results-btn");

    processingDiv.classList.add("hidden");
    processingStatus.textContent = '';
    plagiarismDetectedDiv.innerHTML = "";
    noPlagiarismDiv.innerHTML = "";
    downloadResultsText = ""; // Reset before populating

    let plagiarismFound = false;
    if (data && data.plagiarism_groups && Array.isArray(data.plagiarism_groups) && data.plagiarism_groups.length > 0) {
        plagiarismDetectedDiv.innerHTML = "<h3>🚩 Plagiarized Files</h3>";
        downloadResultsText += "Plagiarism Detected:\n";
        data.plagiarism_groups.forEach(group => {
            const fileList = group.join(', ');
            let p = document.createElement("p");
            p.innerHTML = `Files in this group: <strong>${fileList}</strong>`;
            plagiarismDetectedDiv.appendChild(p);
            downloadResultsText += `Files in this group: ${fileList}\n`;
        });
        downloadResultsBtn.classList.remove("hidden");
        plagiarismFound = true;
    } else {
        plagiarismDetectedDiv.innerHTML = "<h3> No Significant Plagiarism Groups Detected</h3>";
        downloadResultsText += "No Significant Plagiarism Groups Detected\n";
    }

    // Display non-plagiarized files in the desired format
    if (data && data.no_plagiarism_files && Array.isArray(data.no_plagiarism_files) && data.no_plagiarism_files.length > 0) {
        const originalFilesList = data.no_plagiarism_files.join(', ');
        noPlagiarismDiv.innerHTML = `<h4>📄 <strong>Original Files:</strong> ${originalFilesList}</h4>`;
        downloadResultsText += `\nOriginal Files: ${originalFilesList}\n`;
        resultsDiv.classList.remove("hidden");
        downloadResultsBtn.classList.remove("hidden"); // Show download button
    } else if (!plagiarismFound) {
        noPlagiarismDiv.innerHTML = "<p>All processed files appear to be original.</p>";
        downloadResultsText += "All processed files appear to be original.\n";
        resultsDiv.classList.remove("hidden");
        downloadResultsBtn.classList.remove("hidden");
    } else if (!noPlagiarismDiv.innerHTML) {
        noPlagiarismDiv.innerHTML = "<p>No original files found.</p>";
    }

    resultsDiv.classList.remove("hidden");
});


// Attach the download button event listener once when the script loads
document.getElementById('download-results-btn').addEventListener('click', function() {
    const filename = 'plagiarism_results.txt';
    const blob = new Blob([downloadResultsText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
});

// Initial state: hide the processing spinner
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('processing').classList.add('hidden');
});