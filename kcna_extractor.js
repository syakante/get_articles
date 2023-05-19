//given csv of articles, use parallelizing to extract their article text and write them + relevant article metadata to csv
const { extract, getSanitizeHtmlOptions, setSanitizeHtmlOptions } = require('@extractus/article-extractor');
const { parseArgs } = require('node:util');
const path = require('node:path');
const fs = require('fs');
const csv = require('csv');
// const { parse } = require('csv-parse');
// const { createObjectCsvWriter } = require('csv-writer');

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
const kncaRegex = /\(평양\s*\d+월\s*\d+일발\s*조선중앙통신\)(?:\s*\d+일부\s*)?(.*?)\(끝\)/;
setSanitizeHtmlOptions(mySanitizeOptions);

const filepath = 'test.csv';
const header = false;
//for now lets just assume the csv will be a single column. You can future-proof (is that the word?) later with argparse and stuff.
//Just get this working for now aieeeeee

function readCSV() {
  return new Promise((resolve, reject) => {
    const ret = []
    fs.createReadStream(path.join(__dirname, filepath))
      .pipe(csv.parse({ delimiter: ',', from_line: + header+1, encoding: 'utf8' }))
      .on("data", (row) => {
        ret.push(row)
      }).on('error', (err) =>  {
        console.error(err);
        reject(err);
      }).on("end", () => {
      console.log(`read CSV, got ${ret.length} rows`);
      resolve(ret.flat().map(s => s.normalize().trim()));
      });

  })

}

async function getUrlArticleText(input) {
  try {
      const article = await extract(input)
      //console.log(article)
      if(article != null){
        //console.log(`article title is ${article.title}`);
        //rawContent = sanitizeHtml(article.content, { allowedTags: myAllowedTags });
        //console.log(getSanitizeHtmlOptions())
        articleText = article.content.replace(rightTag, '').replace(leftTag, ' ');
        const matches = articleText.match(kncaRegex);
        if(matches) {
          return(matches[1])
        } else {
          console.log("Didn't find a regex match?!");
          return('');
        }
        //console.log(articleText);
        return(articleText[0]);
      } else {
        console.log("Got null. Seems like the webpage needs be rendered with JS client-side.");
      }
    } catch (err) {
      console.error(`Error on ${input}: ${err}`);
    }
}

//TODO: this doesn't work. aiieeeeee
function writeCSV(filePath, data) {
  return new Promise((resolve, reject) => {
    const stream = csv.stringify({ header: true });
    const writableStream = fs.createWriteStream(filePath);

    writableStream.on('error', (err) => {
      reject(err);
    });

    stream.pipe(writableStream).on('finish', () => {
      resolve();
    });

    data.forEach((row) => {
      stream.write(row);
    });

    stream.end();
  });
}

async function main() {
  try {
    const urlArr = await readCSV();
    const textArr = await Promise.all(urlArr.map((url) => getUrlArticleText(url)));
    console.log("ok...");
    //console.log(textArr);
    await writeCSV('output.csv', textArr);
    console.log("ajlsdkfjlsakdfj;sadlkfjkl");
  } catch (err) {
    console.error(err)
  }
}

main();