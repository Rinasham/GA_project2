
function disableCategories(){
  aTags = document.getElementsByClassName('disable-btn')
  for (let i = 0; i < aTags.length; i++) {
    aTags[i].style.pointerEvents = 'none'
  }
}
function disableAnswers(){
  answers = document.getElementsByClassName('answer-submit')
  for (let i = 0; i < answers.length; i++) {
    answers[i].style.pointerEvents = 'none'
  }
}

function disableButton(){
  btn = document.getElementById('go-to-main')
  btn.style.pointerEvents = 'none'
}