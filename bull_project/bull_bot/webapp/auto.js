async function addCourse(payload) {
    const finalPayload = payload + Date.now();
    const resp = await fetch("https://my.sdu.edu.kz/index.php", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": document.cookie
        },
        body: finalPayload
    });
    const text = await resp.text();
    console.log("Ответ сервера для", finalPayload, "->", text);
}
const courses = [
  //"ajx=1&mod=course_reg&action=AddCourse&tid=928&stud=230103269&secN=77013&secP=77016&secL=&secSQ=6579&derskod=INF 362&",
  "ajx=1&mod=course_reg&action=AddCourse&tid=928&stud=230103269&secN=76996&secP=76999&secL=&secSQ=6579&derskod=INF 374&",
      ];
(async () => {
    while (true) {
        for (let payload of courses) {
            await addCourse(payload);
            await new Promise(r => setTimeout(r, 2000)); // 7 секунд
        }
    }
})();