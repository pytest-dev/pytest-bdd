var Gherkin = require("@cucumber/gherkin");
var Messages = require("@cucumber/messages");
var fs = require('fs');

const feature = fs.readFileSync(0, "utf-8");

var uuidFn = Messages.IdGenerator.uuid();
var builder = new Gherkin.AstBuilder(uuidFn);
var matcher = new Gherkin.GherkinInMarkdownTokenMatcher();

var parser = new Gherkin.Parser(builder, matcher);
var gherkinDocument = parser.parse(feature);
console.log(JSON.stringify(gherkinDocument));
