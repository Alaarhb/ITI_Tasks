// shapeModule.js - Shape Class Definition
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

// ===========================================
// IMPLEMENTATION AND DEMONSTRATION
// ===========================================

console.log("=== Shape Class Implementation Demo ===\n");


console.log("1. Creating shape with default color:");
const shape1 = new Shape();
shape1.DrawShape(); 
console.log(`Getter returns: ${shape1.getColor()}\n`);

console.log("2. Creating shape with custom color 'red':");
const shape2 = new Shape('red');
shape2.DrawShape(); 
console.log(`Getter returns: ${shape2.getColor()}\n`);


console.log("3. Changing shape2 color to 'blue' using setter:");
shape2.setColor('blue');
shape2.DrawShape(); 
console.log(`Getter returns: ${shape2.getColor()}\n`);


console.log("4. Creating multiple shapes with different colors:");
const shapes = [
    new Shape('purple'),
    new Shape('green'),
    new Shape('yellow'),
    new Shape('orange')
];

shapes.forEach((shape, index) => {
    console.log(`Shape ${index + 1}:`);
    shape.DrawShape();
});

console.log("\n5. Modifying all shapes to 'pink':");
shapes.forEach((shape, index) => {
    shape.setColor('pink');
    console.log(`Shape ${index + 1}:`);
    shape.DrawShape();
});

console.log("\n6. Testing private property encapsulation:");
const testShape = new Shape('test-color');
console.log("Trying to access private property directly:");
console.log(`testShape.color = ${testShape.color}`); 
console.log(`testShape.#color would cause error (commented out)`);
console.log(`Using getter: ${testShape.getColor()}`); 


export default Shape;

CommonJS:
module.exports = Shape;