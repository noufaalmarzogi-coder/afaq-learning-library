import {
  auth, db, googleProvider, ADMIN_UID,
  signInWithPopup, onAuthStateChanged, signOut,
  collection, addDoc, query, where, onSnapshot,
  serverTimestamp, doc, updateDoc, deleteDoc
} from "./firebase-config.js";

const form = document.getElementById("contribForm");
const exchange = document.getElementById("exchange");
const resources = document.getElementById("resources");
const status = document.getElementById("copyStatus");
const posts = collection(db, "contributions");
let user = null;
let stopPublic = null;
let stopAdmin = null;
let publicSnapshot = null;

const css = document.createElement("style");
css.textContent = `
.afaq-tools{padding:16px;margin:15px 0;border:1px solid #b9dbdb;border-radius:16px;background:#f3fbfa}
.afaq-tools button,.afaq-admin button,.afaq-post button{margin:5px;padding:9px 14px;border:0;border-radius:9px;background:#087b86;color:white;cursor:pointer;font:inherit}
.afaq-posts{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:18px}
.afaq-post{border:1px solid #c9dddd;border-radius:15px;padding:16px;background:white;overflow-wrap:anywhere}
.afaq-post h3{margin:8px 0;color:#075b65}
.afaq-post small{color:#596b71}
.afaq-post p{white-space:pre-line}
.afaq-post a{color:#087b86;text-decoration:underline}
.afaq-admin{margin:18px 0;padding:15px;border:2px solid #087b86;border-radius:15px}
.afaq-admin-item{border-bottom:1px solid #ccc;padding:12px 0}
.afaq-muted{color:#66757a;font-size:.92em}
`;
document.head.append(css);

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function isAdmin() { return !!user && user.uid === ADMIN_UID; }
function say(message) { status.textContent = message; }
function errorText(error) {
  const code = error?.code || "";
  if (code === "auth/unauthorized-domain") return "نطاق المكتبة غير مصرح به لتسجيل الدخول. يجب إضافته في Firebase Console ضمن Authentication ثم Settings ثم Authorized domains.";
  if (code === "auth/operation-not-allowed") return "تسجيل الدخول باستخدام Google غير مفعّل في إعدادات Firebase Authentication.";
  if (code === "auth/popup-closed-by-user") return "أُغلقت نافذة تسجيل الدخول قبل اكتماله. إذا ظهرت صفحة بيضاء، افتحي المكتبة في متصفح مستقل واسمحي بالنوافذ المنبثقة، ثم حاولي مجدداً.";
  if (code === "auth/cancelled-popup-request") return "أُلغيت محاولة تسجيل الدخول بسبب فتح محاولة أخرى. حاولي مجدداً من نافذة واحدة.";
  if (code === "auth/web-storage-unsupported") return "تسجيل الدخول يحتاج إلى تخزين المتصفح. اسمحي ببيانات الموقع وافتحي المكتبة في متصفح مستقل.";
  if (code === "auth/network-request-failed") return "تعذر الاتصال بخدمة تسجيل الدخول. تحققي من الاتصال ومن عدم حجب خدمات Google وFirebase، ثم حاولي مجدداً.";
  if (code.includes("popup-blocked")) return "المتصفح منع نافذة Google. افتحي المكتبة مباشرة في Safari واسمحي بالنوافذ المنبثقة.";
  if (code.includes("permission-denied")) return "رفضت قواعد الأمان العملية. تأكدي من تسجيل الدخول وصحة بيانات المشاركة.";
  return "تعذرت العملية: " + (error?.message || "خطأ غير معروف");
}

const tools = el("div", undefined, "afaq-tools");
const account = el("p", "سجّلي الدخول بحساب Google لنشر مشاركة تعليمية.");
const login = el("button", "تسجيل الدخول باستخدام Google");
login.type = "button";
const logout = el("button", "تسجيل الخروج");
logout.type = "button";
logout.hidden = true;
tools.append(account, login, logout);
form.before(tools);

login.addEventListener("click", async () => {
  if (login.disabled) return;
  login.disabled = true;
  say("أكملي تسجيل الدخول في نافذة Google، ثم انتظري عودتها إلى المكتبة.");
  try {
    await signInWithPopup(auth, googleProvider);
    say("تم تسجيل الدخول بنجاح.");
  }
  catch (error) { say(errorText(error)); }
  finally { login.disabled = false; }
});
logout.addEventListener("click", async () => {
  try { await signOut(auth); }
  catch (error) { say(errorText(error)); }
});

const submit = form.querySelector('button[type="submit"]');
submit.textContent = "نشر المشاركة في المكتبة";
const consent = el("label");
consent.style.display = "block";
consent.style.margin = "14px 0";
const check = document.createElement("input");
check.type = "checkbox";
check.required = true;
consent.append(check, document.createTextNode(" أوافق على نشر اسم المعلمة ومحتوى المشاركة ورابطها للزوار، وأؤكد خلوّها من بيانات الطلاب الشخصية."));
submit.before(consent);

const instructions = document.querySelector("#participate .panel.soft");
if (instructions) {
  instructions.replaceChildren(
    el("h3", "كيف تتم المشاركة؟"),
    el("p", "١. سجّلي الدخول باستخدام حساب Google الخاص بكِ."),
    el("p", "٢. أدخلي اسمكِ، وحددي نوع المشاركة والصف المستهدف، ثم اكتبي عنوان المشاركة ووصفها، وأضيفي الرابط إن وجد."),
    el("p", "٣. اضغطي على زر «نشر المشاركة في المكتبة»."),
    el("p", "٤. ستظهر مشاركتكِ تلقائيًا في قسم «مشاركات المعلمات»."),
    el("p", "٥. يمكنكِ تعديل مشاركاتكِ أو حذفها في أي وقت من خلال قسم «إدارة مشاركاتي» بعد تسجيل الدخول بحسابكِ.")
  );
}
const oldExchangeNotice = exchange.querySelector(".notice");
if (oldExchangeNotice) oldExchangeNotice.textContent = "تظهر هنا المشاركات التعليمية التي تنشرها المعلمات مباشرة.";
const oldResourceEmpty = resources.querySelector(".empty");
if (oldResourceEmpty) oldResourceEmpty.textContent = "تظهر الموارد التي تشاركها المعلمات تلقائياً في هذه المساحة.";

const exchangeList = el("div", undefined, "afaq-posts");
const resourceList = el("div", undefined, "afaq-posts");
exchange.append(exchangeList);
resources.append(resourceList);

const adminPanel = el("section", undefined, "afaq-admin");
adminPanel.hidden = true;
adminPanel.append(el("h3", "لوحة إدارة المشاركات"));
const adminList = el("div");
adminPanel.append(adminList);
tools.after(adminPanel);

function isResource(type) {
  return ["ورقة عمل أو نشاط", "عرض أو وسيلة تعليمية", "اختبار تفاعلي"].includes(type);
}
function canManage(data) {
  return !!user && (isAdmin() || (user.emailVerified && data.authorUid === user.uid));
}

function managementButtons(record) {
  const data = record.data();
  const actions = el("div");
  const edit = el("button", "تعديل");
  const remove = el("button", "حذف");
  edit.type = remove.type = "button";
  remove.style.background = "#a63232";
  edit.addEventListener("click", async () => {
    if (!canManage(data)) return;
    const fields = [
      ["teacher", "اسم المعلمة"], ["title", "عنوان المشاركة"],
      ["description", "وصف المشاركة"], ["url", "الرابط (اختياري)"],
      ["type", "نوع المشاركة"], ["grade", "الصف"]
    ];
    const changes = {};
    for (const [key, label] of fields) {
      const value = prompt(label, data[key] || "");
      if (value === null) return;
      changes[key] = value.trim();
    }
    if (changes.teacher.length < 2 || changes.teacher.length > 100
      || changes.title.length < 3 || changes.title.length > 150
      || changes.description.length < 10 || changes.description.length > 1500) {
      alert("الاسم من حرفين إلى ١٠٠، والعنوان من ٣ إلى ١٥٠، والوصف من ١٠ إلى ١٥٠٠ حرف.");
      return;
    }
    if (changes.url.length > 500 || (changes.url && !/^https:\/\//.test(changes.url))) {
      alert("يجب أن يبدأ الرابط بـ https:// وألا يتجاوز ٥٠٠ حرف.");
      return;
    }
    for (const [key, sourceId] of [["type", "type"], ["grade", "participationGrade"]]) {
      const values = [...document.getElementById(sourceId).options].map(option => option.value);
      if (!changes[key] || !values.includes(changes[key])) {
        alert("يرجى استخدام أحد الخيارات المتاحة في نموذج المشاركة للنوع والصف.");
        return;
      }
    }
    edit.disabled = remove.disabled = true;
    try {
      await updateDoc(doc(db, "contributions", record.id), changes);
      say("تم تعديل المشاركة بنجاح.");
    } catch (error) { alert(errorText(error)); }
    finally { edit.disabled = remove.disabled = false; }
  });
  remove.addEventListener("click", async () => {
    if (!canManage(data) || !confirm("هل تريدين حذف المشاركة «" + data.title + "» نهائياً؟ لا يمكن التراجع.")) return;
    edit.disabled = remove.disabled = true;
    try {
      await deleteDoc(doc(db, "contributions", record.id));
      say("تم حذف المشاركة بنجاح.");
    } catch (error) { alert(errorText(error)); }
    finally { edit.disabled = remove.disabled = false; }
  });
  actions.append(edit, remove);
  return actions;
}

function drawPost(record) {
  const data = record.data();
  const card = el("article", undefined, "afaq-post");
  card.append(el("small", data.type + " • " + data.grade));
  card.append(el("h3", data.title));
  card.append(el("p", data.description));
  card.append(el("small", "مشاركة المعلمة: " + data.teacher));
  if (data.url && /^https:\/\//i.test(data.url)) {
    const link = el("a", "فتح المورد التعليمي");
    link.href = data.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    const div = el("div");
    div.style.marginTop = "10px";
    div.append(link);
    card.append(div);
  }
  return card;
}
function renderPublic(snapshot) {
  publicSnapshot = snapshot;
  exchangeList.replaceChildren();
  resourceList.replaceChildren();
  const items = [...snapshot.docs];
  items.sort((a,b) => (b.data().createdAt?.seconds || 0) - (a.data().createdAt?.seconds || 0));
  for (const item of items) {
    (isResource(item.data().type) ? resourceList : exchangeList).append(drawPost(item));
  }
  if (!exchangeList.childElementCount) exchangeList.append(el("p", "لا توجد مشاركات منشورة حالياً.", "afaq-muted"));
  if (!resourceList.childElementCount) resourceList.append(el("p", "لا توجد موارد منشورة حالياً.", "afaq-muted"));
}

function renderAdmin(snapshot) {
  adminList.replaceChildren();
  if (snapshot.empty) adminList.append(el("p", "لا توجد مشاركات لإدارتها."));
  snapshot.docs.forEach(record => {
    const data = record.data();
    const item = el("div", undefined, "afaq-admin-item");
    item.append(el("strong", data.title + " — " + data.teacher));
    item.append(el("p", data.visible ? "الحالة: ظاهرة للزوار" : "الحالة: مخفية"));
    const toggle = el("button", data.visible ? "إخفاء المشاركة" : "إظهار المشاركة");
    toggle.type = "button";
    toggle.addEventListener("click", async () => {
      toggle.disabled = true;
      try { await updateDoc(doc(db,"contributions",record.id),{visible: !data.visible}); }
      catch (error) { alert(errorText(error)); }
      finally { toggle.disabled = false; }
    });
    if (isAdmin()) item.append(toggle);
    item.append(managementButtons(record));
    adminList.append(item);
  });
}

onSnapshot(query(posts, where("visible","==",true)), renderPublic,
  error => exchangeList.replaceChildren(el("p",errorText(error))));

onAuthStateChanged(auth, current => {
  user = current;
  if (publicSnapshot) renderPublic(publicSnapshot);
  login.hidden = !!user;
  logout.hidden = !user;
  account.textContent = user
    ? "تم تسجيل الدخول: " + (user.displayName || user.email || "مستخدمة Google")
    : "سجّلي الدخول بحساب Google لنشر مشاركة تعليمية.";
  adminPanel.hidden = !user || (!isAdmin() && !user.emailVerified);
  adminPanel.querySelector("h3").textContent = isAdmin() ? "لوحة إدارة المشاركات" : "إدارة مشاركاتي";
  adminList.replaceChildren();
  if (stopAdmin) { stopAdmin(); stopAdmin = null; }
  if (user && (isAdmin() || user.emailVerified)) {
    const managedPosts = isAdmin() ? posts : query(posts, where("authorUid", "==", user.uid));
    stopAdmin = onSnapshot(managedPosts, renderAdmin,
      error => adminList.replaceChildren(el("p",errorText(error))));
  }
});

form.addEventListener("submit", async event => {
  event.preventDefault();
  event.stopImmediatePropagation();
  if (!user) { say("سجّلي الدخول باستخدام Google أولاً."); return; }
  if (!user.emailVerified) { say("يجب استخدام حساب Google ببريد إلكتروني مؤكّد."); return; }
  if (!check.checked) { say("يجب الموافقة على شروط النشر."); return; }
  const value = id => document.getElementById(id).value.trim();
  const data = {
    teacher: value("teacher"),
    type: value("type"),
    grade: value("participationGrade"),
    title: value("resourceTitle"),
    description: value("description"),
    url: value("resourceUrl"),
    visible: true,
    authorUid: user.uid,
    createdAt: serverTimestamp()
  };
  if (data.teacher.length < 2 || data.title.length < 3 || data.description.length < 10) {
    say("يرجى كتابة اسم وعنوان ووصف كافٍ للمشاركة (الوصف ١٠ أحرف على الأقل).");
    return;
  }
  if (data.url && !/^https:\/\//i.test(data.url)) {
    say("يجب أن يبدأ الرابط بـ https://"); return;
  }
  submit.disabled = true;
  say("جارٍ إرسال المشاركة...");
  try {
    await addDoc(posts, data);
    form.reset();
    say("تم نشر المشاركة بنجاح، وستظهر تلقائياً في القسم المناسب.");
  } catch(error) {
    say(errorText(error));
  } finally { submit.disabled = false; }
}, true);

// تنسيق موحد للمشاركات المنشورة في القسمين
const exchangeHeading = el("h3", "مشاركات المعلمات", "afaq-published-heading");
const resourcesHeading = el("h3", "الموارد التعليمية المنشورة", "afaq-published-heading");

const exchangeNotice = exchange.querySelector(".notice");
if (exchangeNotice) exchangeNotice.remove();

const oldResourcesPanel = resources.querySelector(".panel");
if (oldResourcesPanel) oldResourcesPanel.remove();

exchangeList.before(exchangeHeading);
resourceList.before(resourcesHeading);

const layoutStyle = document.createElement("style");
layoutStyle.textContent = ".afaq-published-heading{color:#17384b;font-size:1.35rem;margin:26px 0 10px;padding-bottom:10px;border-bottom:2px solid #c6e0df}.afaq-posts{margin-top:12px}.afaq-posts .afaq-muted{grid-column:1/-1;padding:18px;border-radius:14px;background:#f3fbfa;text-align:center}";
document.head.append(layoutStyle);

// البحث والتصفية في تبادل الخبرات وبنك الموارد
const searchStyle = document.createElement("style");
searchStyle.textContent = ".afaq-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;padding:15px;margin:12px 0;background:#f3fbfa;border:1px solid #c6e0df;border-radius:15px}.afaq-filters input,.afaq-filters select{width:100%;min-width:0;padding:11px;border:1px solid #aecfcf;border-radius:10px;background:white;color:#17384b;font:inherit}.afaq-result-count{grid-column:1/-1;color:#506e75;font-size:.9rem}.afaq-post[hidden]{display:none!important}";
document.head.append(searchStyle);

function makeFilters(list, title) {
  const bar = document.createElement("div");
  bar.className = "afaq-filters";
  bar.setAttribute("aria-label", "البحث في " + title);

  const search = document.createElement("input");
  search.type = "search";
  search.placeholder = "ابحثي عن مشاركة...";
  search.setAttribute("aria-label", "البحث في " + title);

  function makeSelect(sourceId, allLabel) {
    const select = document.createElement("select");
    select.setAttribute("aria-label", allLabel);
    select.add(new Option(allLabel, ""));
    const source = document.getElementById(sourceId);
    if (source) {
      [...source.options].forEach(option => {
        if (option.value && ![...select.options].some(o => o.value === option.value)) {
          select.add(new Option(option.textContent.trim(), option.value));
        }
      });
    }
    return select;
  }

  const grade = makeSelect("participationGrade", "جميع الصفوف");
  const type = makeSelect("type", "جميع أنواع المشاركات");
  const count = document.createElement("div");
  count.className = "afaq-result-count";
  count.setAttribute("aria-live", "polite");
  bar.append(search, grade, type, count);
  list.before(bar);

  function normalize(value) {
    return String(value || "").normalize("NFKC")
      .replace(/[\u064B-\u065F\u0670]/g, "")
      .replace(/[أإآ]/g, "ا").replace(/ى/g, "ي")
      .toLocaleLowerCase("ar").trim();
  }

  function refresh() {
    const cards = [...list.querySelectorAll(".afaq-post")];
    let visible = 0;
    cards.forEach(card => {
      const meta = normalize(card.querySelector("small")?.textContent);
      const text = normalize(card.textContent);
      const matches = text.includes(normalize(search.value))
        && (!grade.value || meta.includes(normalize(grade.selectedOptions[0].text)))
        && (!type.value || meta.includes(normalize(type.selectedOptions[0].text)));
      if (card.hidden === matches) card.hidden = !matches;
      if (matches) visible++;
    });
    count.textContent = (search.value.trim() || grade.value || type.value)
      ? "النتائج: " + visible + " من " + cards.length
        + (visible === 0 ? " — لا توجد مشاركات مطابقة." : "")
      : "عدد المشاركات: " + cards.length;
  }

  [search, grade, type].forEach(control => {
    control.addEventListener("input", refresh);
    control.addEventListener("change", refresh);
  });
  new MutationObserver(refresh).observe(list, {childList:true});
  refresh();
}

makeFilters(exchangeList, "مشاركات المعلمات");
makeFilters(resourceList, "الموارد التعليمية المنشورة");
