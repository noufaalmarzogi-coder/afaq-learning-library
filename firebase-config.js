import { initializeApp } from "https://www.gstatic.com/firebasejs/13.1.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/13.1.0/firebase-auth.js";
import { getFirestore, collection, addDoc, query, where, orderBy, onSnapshot, serverTimestamp, doc, updateDoc, deleteDoc } from "https://www.gstatic.com/firebasejs/13.1.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyAn49-kxu9vJhEDm9SI56h5_pT43lve0KY",
  authDomain: "afaq-learning-library.firebaseapp.com",
  projectId: "afaq-learning-library",
  storageBucket: "afaq-learning-library.firebasestorage.app",
  messagingSenderId: "148517592056",
  appId: "1:148517592056:web:015c5ac2eff48b64a4940d"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

const ADMIN_UID = "Zt6PiTDBwHXLBczySJDzCnyKbvG3";

export {
  app, auth, db, googleProvider, ADMIN_UID,
  signInWithPopup, signInWithRedirect, onAuthStateChanged, signOut,
  collection, addDoc, query, where, orderBy, onSnapshot,
  serverTimestamp, doc, updateDoc, deleteDoc
};
