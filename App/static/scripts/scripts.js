// console.log('working')

let theme = localStorage.getItem('theme')

if (theme === 'light'){
    document.querySelectorAll('*').forEach((element) =>{
        element.classList.forEach((className)=>{
            if(className=== 'dark-theme'){
                element.classList.replace('dark-theme', 'light-theme');
            }
            else if(className=== 'middle-dark-theme'){
                    element.classList.replace('middle-dark-theme', 'middle-light-theme');
            }
            

        })
    
    })
}
if(theme=== 'dark'){
    document.querySelectorAll('*').forEach((element) =>{
        element.classList.forEach((className) =>{
            if(className=== 'light-theme'){
                element.classList.replace('light-theme', 'dark-theme');
            }
            if(className==='user-message'){
                element.style.color ='#000'
                element.style.backgroundColor='#d6d6ddff'
            }
            if(className==='contact-message'){
                // element.style.color ='#000'
                element.style.backgroundColor='#000000fd'
            }
            if(className==='search-bar'){
                element.style.backgroundColor ='#151515'
                element.style.color = '#f5f5f5'
            }
           
            if(className=== 'middle-light-theme'){
                    element.classList.replace('middle-light-theme', 'middle-dark-theme');
            }
        })
    })
}




document.querySelectorAll('.menu-btn').forEach((element) =>{
console.log(element)
element.addEventListener('click', function(){
    this.classList.toggle('clicked')
    let currentName = this.getAttribute('name');
    console.log(currentName)
    closeIcon = 'close-outline'
    let newName = currentName === closeIcon? previousName:closeIcon;
    previousName = currentName;
    this.setAttribute('name', newName);
    
        menu = this.nextElementSibling;
        menu.classList.toggle('show');
// })
});
}

)



document.querySelectorAll('.theme').forEach((element) =>{
    element.addEventListener('click', function(){
        let currentName = this.getAttribute('name');
        console.log(currentName)
        radioOn = 'radio-button-on-outline';
        let newName = currentName === radioOn? previousName:radioOn;
        previousName = currentName;
        this.setAttribute('name', newName);

        console.log('theme');
        theme = localStorage.getItem('theme');
        console.log(theme);
    
    if(theme==='dark'){
        localStorage.setItem('theme', 'light');
        console.log('theme');

        document.querySelectorAll('*').forEach((element) =>{
        element.classList.forEach((className)=>{
            if(className=== 'dark-theme'){
                element.classList.replace('dark-theme', 'light-theme');
            }
            else if(className=== 'middle-dark-theme'){
                    element.classList.replace('middle-dark-theme', 'middle-light-theme');
            }
            

        })
    
    })
    }
    else{
        localStorage.setItem('theme', 'dark');
        console.log('theme');
        document.querySelectorAll('*').forEach((element) =>{
        element.classList.forEach((className) =>{
            if(className=== 'light-theme'){
                element.classList.replace('light-theme', 'dark-theme');
            }
           
            else if(className=== 'middle-light-theme'){
                    element.classList.replace('middle-light-theme', 'middle-dark-theme');
            }
        })
    })
    }
    })
})
