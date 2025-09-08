// SquaresModule.js
import Shape from './Lab-08.4.js';

class Shape {
    #color;

    constructor(color = 'black') {
        this.#color = color;
    }

    setColor(color) {
        this.#color = color;
    }

    getColor() {
        return this.#color;
    }

    DrawShape() {
        console.log(`Shape color: ${this.#color}`);
    }
}

class Rectangle extends Shape {
    constructor(width, height, color = 'black') {
        super(color); 
        this.width = width;
        this.height = height;
    }

    getArea() {
        const area = this.width * this.height;
        console.log(`Rectangle area: ${area}`);

        this.DrawShape();
        
        return area;
    }

    getWidth() {
        return this.width;
    }

    getHeight() {
        return this.height;
    }

    setWidth(width) {
        this.width = width;
    }

    setHeight(height) {
        this.height = height;
    }
}

class Square extends Rectangle {
    constructor(side, color = 'black') {
        super(side, side, color); 
    }

    getArea() {
        const area = this.width * this.height;
        console.log(`Square area: ${area}`);

        this.DrawShape();
        
        return area;
    }

    getSide() {
        return this.width; 
    }

    setSide(side) {
        this.width = side;
        this.height = side;
    }

    setWidth(width) {
        this.width = width;
        this.height = width;
    }

    setHeight(height) {
        this.width = height;
        this.height = height;
    }
}

// ===========================================
// IMPLEMENTATION AND DEMONSTRATION
// ===========================================

console.log("=== SquaresModule Implementation Demo ===\n");


console.log("1. Creating Rectangle instances:");
const rectangle1 = new Rectangle(5, 10, 'red');
console.log(`Rectangle 1: ${rectangle1.getWidth()} x ${rectangle1.getHeight()}, color: ${rectangle1.getColor()}`);
rectangle1.getArea();

console.log();

const rectangle2 = new Rectangle(8, 6, 'blue');
console.log(`Rectangle 2: ${rectangle2.getWidth()} x ${rectangle2.getHeight()}, color: ${rectangle2.getColor()}`);
rectangle2.getArea();

console.log("\n" + "=".repeat(50) + "\n");

console.log("2. Creating Square instances:");
const square1 = new Square(7, 'green');
console.log(`Square 1: ${square1.getSide()} x ${square1.getSide()}, color: ${square1.getColor()}`);
square1.getArea();

console.log();

const square2 = new Square(4, 'purple');
console.log(`Square 2: ${square2.getSide()} x ${square2.getSide()}, color: ${square2.getColor()}`);
square2.getArea();

console.log("\n" + "=".repeat(50) + "\n");


console.log("3. Modifying properties:");

console.log("Changing rectangle1 dimensions to 12 x 8:");
rectangle1.setWidth(12);
rectangle1.setHeight(8);
rectangle1.getArea();

console.log();

console.log("Changing square1 side to 9:");
square1.setSide(9);
square1.getArea();

console.log();

console.log("Changing colors:");
rectangle1.setColor('yellow');
square1.setColor('orange');

console.log("Rectangle1 after color change:");
rectangle1.getArea();

console.log("Square1 after color change:");
square1.getArea();

console.log("\n" + "=".repeat(50) + "\n");


console.log("4. Inheritance demonstration:");
console.log(`rectangle1 instanceof Rectangle: ${rectangle1 instanceof Rectangle}`);
console.log(`rectangle1 instanceof Shape: ${rectangle1 instanceof Shape}`);
console.log(`square1 instanceof Square: ${square1 instanceof Square}`);
console.log(`square1 instanceof Rectangle: ${square1 instanceof Rectangle}`);
console.log(`square1 instanceof Shape: ${square1 instanceof Shape}`);

console.log("\n" + "=".repeat(50) + "\n");


console.log("5. Working with mixed shapes:");
const shapes = [
    new Rectangle(3, 4, 'cyan'),
    new Square(6, 'magenta'),
    new Rectangle(10, 2, 'lime'),
    new Square(5, 'pink')
];

shapes.forEach((shape, index) => {
    console.log(`\nShape ${index + 1}:`);
    if (shape instanceof Square) {
        console.log(`Type: Square, Side: ${shape.getSide()}, Color: ${shape.getColor()}`);
    } else {
        console.log(`Type: Rectangle, Dimensions: ${shape.getWidth()} x ${shape.getHeight()}, Color: ${shape.getColor()}`);
    }
    shape.getArea();
});


export { Rectangle, Square };

CommonJS:
 module.exports = { Rectangle, Square };