/**
 * Zoom Box: A div to represent the box that surrounds the cursor and outlines the zoomed portion of the image while the user hovers over the original image. We'll reference this element as this.zoomBox.
 * Zoom Container: A div to wrap the original image and the zoom box. Its job is to support positioning the zoom box over the image, so it should be the same size as the image. Well reference it as this.zoomContainer.
 * Zoomed Image: A copy of the original image that we'll allow to grow to its full size so it can be "zoomed". For this effect to work well, the layout in which the image zoomer component is used should display the original image at a much smaller size than it's true size. We'll reference the zoomed image as this.zoomedImage.
 * Zoom Window: A div to contain the zoomed image. It should be smaller than the full size of the image to ensure that only a portion of the zoomed image is visible. We'll move the zoomed image around inside the zoom window as the user moves the mouse cursor over the original image. We'll reference the zoom window as this.zoomWindow.
 **/

class ImageZoomer{
    constructor(image){
        let parentEl = image.parentNode;
        this.image = image;

        this.zoomedImage = image.cloneNode();
        this.zoomWindow = createZoomWindow(this.zoomedImage);

        this.zoomBox = createZoomBox();
        this.zoomContainer = createZoomContainer(image, this.zoomBox);

        parentEl.appendChild(this.zoomContainer);
        parentEl.appendChild(this.zoomWindow);

        sizeZoomBox(this.zoomBox, image, this.zoomWindow, this.zoomedImage);

        this.activate = this.activate.bind(this);
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.listenForMouseEnter();

        this.imageBounds = toDocumentBounds(image.getBoundingClientRect());
        this.zoomBoxBounds = toDocumentBounds(this.zoomBox.getBoundingClientRect());
    }

    activate() {
        this.zoomBox.classList.add('activate');
        this.zoomWindow.classList.add('activate');
        this.listenForMouseMove();
    }

    deactivate(){
        this.zoomBox.classList.remove('activate');
        this.zoomWindow.classList.remove('activate');
        this.listenForMouseEnter();
    }

    handleMouseMove(event){
        if (this.isMoveScheduled){
            return;
        }

        window.requestAnimationFrame(() => {
            if(isWithinImage(this.imageBounds, event)){
                this.updateUI(event.pageX, event.pageY);
            } else {
                this.deactivate();
            }
            this.isMoveScheduled = false;
        });
        this.isMoveScheduled = true;
    }

    listenForMouseEnter(){
        let { image, zoomBox} = this;
        document.body.removeEventListener('mousemove', this.handleMouseMove);
        image.addEventListener('mouseenter', this.activate);
        zoomBox.addEventListener('mouseenter', this.activate);
    }

    listenForMouseMove(){
        let { image, zoomBox } = this;
        image.removeEventListener('mouseenter', this.activate);
        zoomBox.removeEventListener('mouseenter', this.activate);
        document.body.addEventListener('mousemove', this.handleMouseMove)
    }

    moveZoomedImage(xPercent, yPercent){
        let {zoomedImage} = this;
        let xOffset = Math.round(zoomedImage.clientWidth * xPercent) * -1;
        let yOffset = Math.round(zoomedImage.clientHeight * yPercent) * -1;
        zoomedImage.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
    }

    updateUI(mouseX, mouseY){
        let { imageBounds, zoomBox, zoomBoxBounds } = this;
        let { x: xOffset, y: yOffset } = getZoomBoxOffset(mouseX, mouseY, zoomBoxBounds, imageBounds);
        zoomBox.style.transform = `translate(${xOffset}px, ${yOffset}px)`;

        this.moveZoomedImage(xOffset / imageBounds.width, yOffset / imageBounds.height);
    }
}

function createZoomBox(){
    let zoomBox = document.createElement('div');
    zoomBox.classList.add('zoom-box');
    return zoomBox
}

function createZoomContainer(image, zoomBox){
    let zoomContainer = document.createElement('div');
    zoomContainer.classList.add('zoom-container');
    zoomContainer.appendChild(image);
    zoomContainer.appendChild(zoomBox);
    return zoomContainer
}

function createZoomWindow(zoomedImage){
    let zoomWindow = document.createElement('div');
    zoomWindow.classList.add('zoom-window');

    zoomedImage.setAttribute('aria-hidden', 'true');
    zoomWindow.appendChild(zoomedImage);
    return zoomWindow
}

let image = document.querySelector('preview-zoom');
let zoomer = new ImageZoomer(image)

function sizeZoomBox(zoomBox, image, zoomWindow, zoomedImage){
    let widthPercentage = zoomWindow.clientWidth / zoomedImage.clientWidth;
    let heightPercentage = zoomWindow.clientHeight / zoomedImage/clientHeight;

    zoomBox.style.width = Math.round(image.clientWidth * widthPercentage) + 'px';
    zoomBox.style.height = Math.round(image.clientHeight * heightPercentage) + 'px';
}

function isWithinImage(imageBounds, event){
    let {bottom, left, right, top} = imageBounds;
    let { pageX, pageY} = event;

    return pageX > left && pageX < right && pageY > top && pageY < bottom;
}

function toDocumentBounds(bounds){
    let { scrollX, scrollY } = window;
    let { bottom, height, left, right, top, width } = bounds;

    return {
        bottom: bottom + scrollY,
        height,
        left: left + scrollX,
        right: right + scrollX,
        top: top + scrollY,
        width
    }
}

function getZoomBoxOffset(mouseX, mouseY, zoomBoxBounds, imageBounds){
    let x = mouseX - (zoomBoxBounds.width / 2);
    let y = mouseY - (zoomBoxBounds.height / 2);

    x = containNum(x, imageBounds.left, imageBounds.right - zoomBoxBounds.width);
    y = containNum(y, imageBounds.top, imageBounds.bottom - zoomBoxBounds.height);

    x -= zoomBoxBounds.left;
    y -= zoomBoxBounds.top;

    return {x: Math.round(x), y: Math.round(y)}
}

function containNum(num, lowerBound, upperBound){
    if (num < lowerBound){
        return lowerBound;
    }

    if (num > upperBound){
        return upperBound;
    }
    return num;
}