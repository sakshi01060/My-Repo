// Fetch JSON data from REST API
fetch("https://jsonplaceholder.typicode.com/users")
  .then(response => response.json())
  .then(people => {
    console.log("All People Data:", people);

    // Example: Search for a person by name (case-insensitive)
    const searchName = "Leanne Graham".toLowerCase();

    console.log("=== find() ===");
    // find() → Get first person with this name
    const personFind = people.find(p => p.name.toLowerCase() === searchName);
    console.log(personFind);

    console.log("=== filter() ===");
    // filter() → Get all people with this name
    const personFilter = people.filter(p => p.name.toLowerCase() === searchName);
    console.log(personFilter);

    console.log("=== forEach() ===");
    // forEach() → Loop through and print matches
    people.forEach(p => {
      if (p.name.toLowerCase() === searchName) {
        console.log(p);
      }
    });

    console.log("=== map() ===");
    // map() → Extract all names
    const names = people.map(p => p.name);
    console.log(names);

    console.log("=== some() ===");
    // some() → Check if at least one match exists
    const exists = people.some(p => p.name.toLowerCase() === searchName);
    console.log(exists); // true or false

    console.log("=== every() ===");
    // every() → Check if ALL people are from a certain city
    const allFromCity = people.every(p => p.address.city !== "");
    console.log(allFromCity); // true if no one has empty city
  })
  .catch(error => console.error("Error fetching data:", error));
