const express = require('express');
const app = express();
var fs = require('fs');

const myHeader = require('./naver_headers.json');
const headers = new Headers(myHeader);

// app.get('/search/blog', function (req, res) {
//    const api_url = 'https://openapi.naver.com/v1/search/blog?query=' + encodeURI(req.query.query); // JSON 결과
// //   var api_url = 'https://openapi.naver.com/v1/search/blog.xml?query=' + encodeURI(req.query.query); // XML 결과
//    const request = require('request');
//    const options = {
//        url: api_url,
//        headers: {'X-Naver-Client-Id':client_id, 'X-Naver-Client-Secret': client_secret}
//     };
//    request.get(options, function (error, response, body) {
//      if (!error && response.statusCode == 200) {
//        res.writeHead(200, {'Content-Type': 'text/json;charset=utf-8'});
//        res.end(body);
//      } else {
//        res.status(response.statusCode).end();
//        console.log('error = ' + response.statusCode);
//      }
//    });
//  });
//  app.listen(3000, function () {
//    console.log('http://127.0.0.1:3000/search/blog?query=검색어 app listening on port 3000!');
//  });

const options = {
        path: '/',
        method: 'GET',
        headers,
        "Content-Type": "text/json;charset=utf-8",
}

const myQuery = process.argv[2]
const startDate = process.argv[3]
//const endDate = process.argv[4]

//const myQuery = "Victor+Cha" + "&ds=2023.05.01&de=2023.05.24" + "&nso=so%3Add%2Cp%3Afrom20230501to20230524";
//const myQuery = "Victor+Cha&ds=2023.05.01&de=2023.05.24&nso=so%3Add%2Cp%3Afrom20230501to20230524"
//const myQuery = "\"Beyond Parallel\""
async function test() {
  try {
    let articleArray = []
    let saveResponse = await fetch(`https://openapi.naver.com/v1/search/news.json?query=${myQuery}&display=100&start=1&sort=date`, options);
    console.log(encodeURIComponent(myQuery));
    let jsonResponse = await saveResponse.json()
    articleArray = jsonResponse.items.slice()
    //console.log(h.items[99]);
    let fetchDate = Date.parse(articleArray[articleArray.length-1].pubDate) //articleArray.length-1 = 99
    //const startDate = Date.parse("01 Dec 2021 00:00:00 GMT") //or whatever the desired start date is
    let page = 0
    let i = 0
    //console.log(`fetchDate:${fetchDate}`) //date of the 100th, i.e. oldest, article
    while (fetchDate > startDate) {
      console.log("Last item's date does not exceed threshold (too recent, need to search more)")
      i++;
      page = (100*i)+1
      saveResponse = await fetch(`https://openapi.naver.com/v1/search/news.json?query=${myQuery}&display=100&start=${page}&sort=date`, options);
      jsonResponse = await saveResponse.json();
      //jsonResponse.items is an array of len 100, each item in the array being a json object representing an article.
      articleArray.push(...jsonResponse.items);
      fetchDate = Date.parse(articleArray[articleArray.length-1].pubDate);
    }
    console.log("Out of while loop.")
    if (fetchDate < startDate) {
      //2022-12-01
      console.log("Last item's date exceeds threshold (too old, need to cut down)")
      let left = 0;
      let right = articleArray.length-1;
      let result = -1;
      while(left <= right){
        const mid = Math.floor((left+right)/2);
        console.log(mid)
        if(Date.parse(articleArray[mid].pubDate) >= startDate) {
          //console.log("here");
          result = mid;
          left = mid + 1;  
        } else {
          //console.log(jsonResponse.items[mid].pubDate)
          //console.log("here2");
          right = mid - 1;
        }
      }
      //console.log(result)
      console.log(articleArray[result]);
      const FileSystem = require("fs");
      fs.writeFile('naver_out.json', JSON.stringify(articleArray.slice(0, result+1)), (error) => {
        if (error) throw error;
      });
    }
    console.log("ok");
  } catch (err) {
    console.error(err);
  }
}

test()