
function disableCategories(){
  aTags = document.getElementsByClassName('disable-btn')
  for (let i = 0; i < aTags.length; i++) {
    aTags[i].style.pointerEvents = 'none'
  }
}


function disableAnswers(event){
  event.preventDefault()

  const chosenAnswer  = event.target.value
  const answers = document.getElementsByClassName('answer-submit')
  let clickCount = 0
  const guideBtn = document.getElementById('click-next')

  guideBtn.style.visibility = 'visible'

  for (let i = 0; i < answers.length; i++) {
    answers[i].style.pointerEvents = 'none'
  }
  const options = document.getElementsByClassName('options')
  forms = document.querySelectorAll('form')
  for(let i=0; i < options.length; i++){
    const option = options[i]
    if(option.value == answer){
      forms[i].style.background = '#4C7373'
      answers[i].style.color = '#fff'

      // if the click is the second one, submit form
      area = document.querySelector('main')
      area.addEventListener('click', function(){
        clickCount += 1
        console.log(clickCount);
        if(clickCount >= 2){
          form = forms[i].submit()
        }
      })
    } else if(chosenAnswer == option.value) {
        forms[i].style.background = '#8C323A'
        answers[i].style.color = '#fff'
    }
  }
}




function disableButton(){
  btn = document.getElementById('disable')
  btn.style.pointerEvents = 'none'
}
