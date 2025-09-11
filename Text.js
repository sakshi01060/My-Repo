// Example JSON data (array of people)
const people = [
  { id: 1, name: "Alice", age: 25, city: "New York" },
  { id: 2, name: "Bob", age: 30, city: "London" },
  { id: 3, name: "Alice", age: 27, city: "Paris" },
  { id: 4, name: "Charlie", age: 28, city: "Berlin" }
];

console.log("=== Using find() ===");
// 1. find(): Get the first person whose name is "Alice"
const personFind = people.find(p => p.name === "Alice");
console.log(personFind);
// { id: 1, name: "Alice", age: 25, city: "New York" }

console.log("=== Using filter() ===");
// 2. filter(): Get all people whose name is "Alice"
const personFilter = people.filter(p => p.name === "Alice");
console.log(personFilter);
// [ { id: 1, ... }, { id: 3, ... } ]

console.log("=== Using forEach() ===");
// 3. forEach(): Loop through and print people named "Alice"
people.forEach(p => {
  if (p.name === "Alice") {
    console.log(p);
  }
});

console.log("=== Using map() ===");
// 4. map(): Extract all names (not direct search, but useful)
const names = people.map(p => p.name);
console.log(names);
// [ "Alice", "Bob", "Alice", "Charlie" ]

console.log("=== Using some() ===");
// 5. some(): Check if at least one "Alice" exists
const exists = people.some(p => p.name === "Alice");
console.log(exists); // true

console.log("=== Using every() ===");
// 6. every(): Check if all people are older than 18
const allAdults = people.every(p => p.age >= 18);
console.log(allAdults); // true
