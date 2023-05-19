//given csv of articles, use parallelizing to extract their article text and write them + relevant article metadata to csv
const { extract, getSanitizeHtmlOptions, setSanitizeHtmlOptions } = require('@extractus/article-extractor');
const { parseArgs } = require('node:util');
const path = require('node:path');
const fs = require('fs');
const { parse } = require('csv-parse');

//const filepath = process.argv.slice(2)[0]; //aiieeeee

// const options = { filepath: { type: 'string', short: 'f' }, colName: { type: 'string', short: 'c' }, header: { type: 'boolean', short: 'h'} };

// const {
//   values: { filepath, colName, header},
// } = parseArgs({ options });

const mySanitizeOptions = {
  allowedTags: ['p'],
  allowedAttributes: {}
}
const rightTag = /<\/(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+>/g;
const leftTag = /<(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+>/g;
setSanitizeHtmlOptions(mySanitizeOptions);

const filepath = 'test.csv';
const header = false;

function readCSV() {
  return new Promise((resolve, reject) => {
    const ret = []
    fs.createReadStream(path.join(__dirname, filepath))
      .pipe(parse({ delimiter: ',', from_line: + header+1, encoding: 'utf8' }))
      .on("data", (row) => {
        ret.push(row)
      }).on('error', (err) =>  {
        console.error(err);
        reject(err);
      }).on("end", () => {
      console.log(`read CSV, got ${ret.length} rows`)
      resolve(ret);
      });

  })

}

async function main() {
  try {
    const data = await readCSV();
    console.log(data);
    //do stuff
  } catch (err) {
    console.error(err)
  }
}

main();

async function getUrlArticleText() {
  try {
      const article = await extract(input)
      //console.log(article)
      if(article != null){
        console.log(`article title is ${article.title}`);
        //rawContent = sanitizeHtml(article.content, { allowedTags: myAllowedTags });
        //console.log(getSanitizeHtmlOptions())
        articleText = article.content.replace(rightTag, '').replace(leftTag, ' ');
        console.log(articleText);
        return
      } else {
        console.log("Got null. Seems like the webpage needs be rendered with JS client-side.");
      }
    } catch (err) {
      console.error(err);
    }
}