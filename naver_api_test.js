const express = require('express');
const app = express();

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

//const myQuery = "Victor+Cha" + "&ds=2023.05.01&de=2023.05.24" + "&nso=so%3Add%2Cp%3Afrom20230501to20230524";
//const myQuery = "Victor+Cha&ds=2023.05.01&de=2023.05.24&nso=so%3Add%2Cp%3Afrom20230501to20230524"
const myQuery = "\"Victor Cha\""
async function test() {
  try {
    const saveResponse = await fetch(`https://openapi.naver.com/v1/search/news.json?query=${myQuery}&start=2&sort=date`, options);
    console.log(encodeURIComponent(myQuery));
    const h = await saveResponse.json()
    console.log(h);
  } catch (err) {
    console.error(err);
  }
}

test()