$(document).ready(function () {


  $('.fa-bars').click(function () {
    $(this).toggleClass('fa-times');
    $('.navbar').toggleClass('nav-toggle');
  });

  $(window).on('load scroll', function () {
    $('.fa-bars').removeClass('fa-times');
    $('.navbar').removeClass('nav-toggle');

    if ($(window).scrollTop() > 30) {
      $('.header').css({
        'background': '#6C5CE7',
        'box-shadow': '0 .2rem .5rem rgba(0,0,0,.4)'
      });
    } else {
      $('.header').css({
        'background': 'none',
        'box-shadow': 'none'
      });
    }
  });


  $('.accordion-header').click(function () {
    $('.accordion .accordion-body').slideUp();
    $(this).next('.accordion-body').slideDown();
    $('.accordion .accordion-header span').text('+');
    $(this).children('span').text('-');
  });
});


let arrow = document.querySelectorAll(".arrow");
for (var i = 0; i < arrow.length; i++) {
  arrow[i].addEventListener("click", (e) => {
    let arrowParent = e.target.parentElement.parentElement; //selecting main parent of arrow
    arrowParent.classList.toggle("showMenu");
  });
}
let sidebar = document.querySelector(".sidebar");
let sidebarBtn = document.querySelector(".bx-menu");

const button = document.querySelector("#file-upload-btn");
const input = document.querySelector(".form-input-file");

let file; // this is a global variable and we'll use it inside multiple function
const inputSec = document.querySelector(".input-img");
const outputSec = document.querySelector(".output-img");

const imgIn = document.querySelector(".input-section .input-img .image");
const rstIn = document.querySelector(".output-section .result-img .image");

// const wrapperIn = document.querySelector(".result-section .input-img");

const fileName = document.querySelector(".file-name");
const cancelBtn = document.querySelector("#cancel-btn");
let regExp = /[0-9a-zA-Z\^\&\'\@\{\}\[\]\,\$\=\!\-\#\(\)\.\%\+\~\_ ]+$/;

input.addEventListener("change", function () {
  console.log("CHANGE")
  // getting user select file and [0] this means if user select multiple files then we'll select only the first one
  file = this.files[0];
  showFile(); //calling function

  if (this.value) {
    let valueStore = this.value.match(regExp);
    fileName.textContent = valueStore;
    document.getElementById('form-uploader').submit();
  }
});


function showFile() {
  let fileType = file.type;
  let validExtentiton = ["image/jpeg", "image/jpg", "image/png"]; // adding some valid extention in array
  if (validExtentiton.includes(fileType)) { //if user selected file is an image
    // console.log("This is an image file");
    let fileReader = new FileReader(); // creating new FileReader object
    fileReader.onload = () => {
      let fileURL = fileReader.result; //passing user file source in fileURL variable
      // console.log(fileURL);
      let imgTag = `<img src="${fileURL}" alt="">` //creating an img tag and passing user selected file source inside src attribute

      // dropArea.innerHTML = imgTag; //adding that created img tag inside dropArea container
      // window.location.href = 'result.html';
      imgIn.innerHTML = imgTag;
      inputSec.classList.add("active");

      // inputSec.classList.add("hidden");
      // outputSec.classList.remove("hidden");

    }
    cancelBtn.addEventListener("click", function () {
      imgIn.innerHTML = "";
      inputSec.classList.remove("active");

      // inputSec.classList.remove("hidden");
      // outputSec.classList.add("hidden");

      // var a = document.getElementById('#segmentation'); //or grab it by tagname etc
      // a.href = ""
    });
    fileReader.readAsDataURL(file);

  } else {
    alert("This is not an image file");
    // dropArea.classList.remove("active");
    // dragText.textContent = "Drag & Drop to Upload File";
  }

}