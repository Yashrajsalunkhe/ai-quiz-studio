const form = document.querySelector('#quiz-form');
const status = document.querySelector('#status');
const generateButton = document.querySelector('#generate');
const results = document.querySelector('#results');
const questionsContainer = document.querySelector('#questions');
const downloads = document.querySelector('#downloads');
const practiceArea = document.querySelector('#practice-area');
let quiz = [];

function selectedSource() { return document.querySelector('input[name="source"]:checked').value; }
function setStatus(message, kind = '') { status.textContent = message; status.className = `status ${kind}`; }
function escapeHtml(value) { const node = document.createElement('span'); node.textContent = value; return node.innerHTML; }

function updateSourceFields() {
  const source = selectedSource();
  document.querySelector('#text-field').classList.toggle('hidden', source !== 'Paste Text');
  document.querySelector('#pdf-field').classList.toggle('hidden', source !== 'Upload PDF');
}
document.querySelectorAll('input[name="source"]').forEach(input => input.addEventListener('change', updateSourceFields));

function downloadLink(text, filename, type, label) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = filename; link.className = 'download'; link.textContent = label;
  link.addEventListener('click', () => setTimeout(() => URL.revokeObjectURL(url), 1000), { once: true });
  return link;
}

function base64ToBlob(base64, type) {
  const raw = atob(base64), bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) bytes[i] = raw.charCodeAt(i);
  return new Blob([bytes], { type });
}

function renderQuestions() {
  questionsContainer.replaceChildren();
  quiz.forEach((question, index) => {
    const card = document.createElement('article'); card.className = 'question';
    card.innerHTML = `<h3><span class="number">${index + 1}.</span>${escapeHtml(question.question)}</h3><div class="options">${question.options.map((option, optionIndex) => `<div class="option"><b>${String.fromCharCode(65 + optionIndex)}.</b> ${escapeHtml(option)}</div>`).join('')}</div>`;
    questionsContainer.append(card);
  });
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const source = selectedSource();
  const pdf = document.querySelector('#pdf').files[0];
  if (source === 'Upload PDF' && !pdf) return setStatus('Choose a PDF before generating.', 'error');
  if (pdf && pdf.size > 3 * 1024 * 1024) return setStatus('Choose a PDF smaller than 3 MB.', 'error');
  const payload = { source, topic: document.querySelector('#topic').value, text: document.querySelector('#text').value, question_count: Number(document.querySelector('#question-count').value), difficulty: document.querySelector('#difficulty').value, question_type: document.querySelector('#question-type').value, language: document.querySelector('#language').value, bloom: document.querySelector('#bloom').value };
  if (pdf) payload.pdf_base64 = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(',')[1]); reader.onerror = reject; reader.readAsDataURL(pdf); });
  generateButton.disabled = true; setStatus('Generating your quiz… this can take a moment.'); results.classList.add('hidden');
  try {
    const response = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const responseText = await response.text();
    let data;
    try {
      data = JSON.parse(responseText);
    } catch {
      throw new Error(response.ok ? 'The API returned an invalid response.' : `API request failed (${response.status}). Redeploy the Vercel project and check its function logs.`);
    }
    if (!response.ok) throw new Error(data.error || 'Quiz generation failed.');
    quiz = data.questions; renderQuestions(); downloads.replaceChildren(downloadLink(data.csv, 'quiz.csv', 'text/csv;charset=utf-8', 'Download CSV'));
    const pdfLink = document.createElement('a'); const pdfUrl = URL.createObjectURL(base64ToBlob(data.pdf_base64, 'application/pdf'));
    pdfLink.href = pdfUrl; pdfLink.download = 'quiz.pdf'; pdfLink.className = 'download'; pdfLink.textContent = 'Download PDF'; pdfLink.addEventListener('click', () => setTimeout(() => URL.revokeObjectURL(pdfUrl), 1000), { once: true }); downloads.append(pdfLink);
    results.classList.remove('hidden'); setStatus(`${quiz.length} questions generated with ${data.model}.`, 'success'); results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) { setStatus(error.message || 'Could not generate the quiz.', 'error'); }
  finally { generateButton.disabled = false; }
});

document.querySelector('#start-practice').addEventListener('click', () => {
  let current = 0, score = 0;
  practiceArea.classList.remove('hidden');
  function render() {
    if (current === quiz.length) { practiceArea.innerHTML = `<div class="feedback correct"><strong>Quiz complete!</strong> Your score: ${score}/${quiz.length}.</div>`; return; }
    const question = quiz[current];
    practiceArea.innerHTML = `<p><strong>Question ${current + 1} of ${quiz.length}</strong></p><h3>${escapeHtml(question.question)}</h3>${question.options.map((option, index) => `<button class="practice-choice" data-index="${index}" type="button">${String.fromCharCode(65 + index)}. ${escapeHtml(option)}</button>`).join('')}<div id="feedback"></div>`;
    practiceArea.querySelectorAll('.practice-choice').forEach(button => button.addEventListener('click', () => {
      const choice = Number(button.dataset.index), correct = choice === question.answer_index;
      if (correct) score += 1;
      practiceArea.querySelectorAll('.practice-choice').forEach(choiceButton => choiceButton.disabled = true);
      document.querySelector('#feedback').innerHTML = `<div class="feedback ${correct ? 'correct' : 'incorrect'}"><strong>${correct ? 'Correct!' : `Not quite. The answer is ${String.fromCharCode(65 + question.answer_index)}.`}</strong><br>${escapeHtml(question.explanation)}</div><button class="secondary next" type="button">${current + 1 === quiz.length ? 'See score' : 'Next question'}</button>`;
      practiceArea.querySelector('.next').addEventListener('click', () => { current += 1; render(); });
    }));
  }
  render(); practiceArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
});
