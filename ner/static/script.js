function toggleMenu() {
  const menu = document.getElementById("sideMenu");
  menu.classList.toggle("hidden");
}

// File selection handler
document.getElementById('file').addEventListener('change', function () {
  const fileNameDisplay = document.getElementById('file-name');

  if (this.files.length > 0) {
      fileNameDisplay.textContent = `📁 Selected File: ${this.files[0].name}`;
      fileNameDisplay.classList.remove('hidden');
  } else {
      fileNameDisplay.textContent = 'No file chosen';
      fileNameDisplay.classList.add('hidden');
  }
});

// Upload form handler
document.getElementById('upload-form').addEventListener('submit', async function (e) {
  e.preventDefault();

  const loader = document.getElementById('loader');
  const result = document.getElementById('result');

  loader.classList.remove('hidden');
  result.classList.add('hidden');

  const formData = new FormData();
  formData.append('file', document.getElementById('file').files[0]);

  try {
      const response = await fetch('/ner/upload', {
          method: 'POST',
          body: formData,
      });

      if (response.ok) {
          const data = await response.json();
          if (data.error) {
              alert('Error: ' + data.error);
          } else if (data.message) {
              alert(data.message);
              displayEntities([]); // Display empty table if no text extracted
          } else {
              displayEntities(data);
          }
      } else {
          const errorData = await response.json();
          alert('Failed to extract entities. Please try again.\n' + (errorData.error || ''));
      }
  } catch (error) {
      alert('Error: ' + error.message);
  } finally {
      loader.classList.add('hidden');
  }
});

// Display extracted entities
function displayEntities(entities) {

  const tableBody = document.querySelector('#entityTable tbody');
  const filterSelect = document.getElementById('entityFilter');
  const totalEntitiesDisplay = document.getElementById('totalEntities');
  const entitySummaryDisplay = document.getElementById('entitySummary');
  const downloadCSVBtn = document.getElementById('downloadCSV');
  const downloadExcelBtn = document.getElementById('downloadExcel');

  tableBody.innerHTML = '';
  filterSelect.innerHTML = '<option value="All">All</option>';

  const labels = new Map();
  entities.forEach(entity => {
      const label = entity[1];
      const labelText = labelDefinitions[label] || "Entity type";

      // Create table row with tooltip
      const row = `
          <tr>
              <td>${entity[0]}</td>
              <td data-title="${labelText}">${label}</td>
          </tr>`;
      tableBody.innerHTML += row;
      labels.set(label, (labels.get(label) || 0) + 1);
  });

  totalEntitiesDisplay.textContent = entities.length;
  entitySummaryDisplay.textContent = Array.from(labels)
      .map(([label, count]) => `${label}: ${count}`)
      .join(', ');

  labels.forEach((_, label) => {
      filterSelect.innerHTML += `<option value="${label}">${label}</option>`;
  });

  document.getElementById('result').classList.remove('hidden');
  downloadCSVBtn.classList.remove('hidden');
  downloadExcelBtn.classList.remove('hidden');
}

// Filter dropdown logic
document.getElementById('entityFilter').addEventListener('change', function () {
  const selectedLabel = this.value;
  const rows = document.querySelectorAll('#entityTable tbody tr');

  rows.forEach(row => {
      const label = row.children[1].textContent;
      row.style.display = (selectedLabel === 'All' || label === selectedLabel) ? '' : 'none';
  });
});

// Download CSV
document.getElementById('downloadCSV').addEventListener('click', function () {
  const rows = document.querySelectorAll('#entityTable tbody tr');
  if (!rows.length) return alert('No entities to download!');

  let csv = 'Entity,Label\n';
  rows.forEach(row => {
      const entity = row.children[0].textContent;
      const label = row.children[1].textContent;
      csv += `"${entity}","${label}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'extracted_entities.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
});

// Download Excel
document.getElementById('downloadExcel').addEventListener('click', function () {
  const rows = document.querySelectorAll('#entityTable tbody tr');
  if (!rows.length) return alert('No entities to download!');

  const wb = XLSX.utils.book_new();
  const data = [['Entity', 'Label']];

  rows.forEach(row => {
      const entity = row.children[0].textContent;
      const label = row.children[1].textContent;
      data.push([entity, label]);
  });

  const ws = XLSX.utils.aoa_to_sheet(data);
  XLSX.utils.book_append_sheet(wb, ws, 'Entities');
  XLSX.writeFile(wb, 'extracted_entities.xlsx');
});