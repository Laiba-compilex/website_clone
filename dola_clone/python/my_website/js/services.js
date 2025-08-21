// const axios = require('axios');
// import JsonFormate from "./JsonFormate";
// import * as services from './index.js';
var gameCategories = [];
async function fetchBaseURL() {
  try {
    const response = await fetch(
      "https://cdntracker0019.com?site_code=staging"
    );
    const data = await response.json();

    if (response?.status === 200 && data?.url) {
      console.log("Base URL fetched successfully:", data.url);
      return data.url;
    } else {
      throw new Error("Invalid response for base URL");
    }
  } catch (error) {
    console.error("Error fetching base URL:", error);
    throw error;
  }
}

async function getGameCategories() {
  const BaseUrl = await fetchBaseURL();
  if (!BaseUrl) {
    console.error("Base URL is not defined");
    return null;
  }

  try {
    const response = await fetch(`${BaseUrl}/api/player/game_categories`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        accept: "application/json",
      },
    });
    console.log("Response status:", response);
    // if (response.ok) {
    const data = await response.json();
    console.log("Game categories fetched successfully:", data);
    return data;
    // }
    if (response.status === 500) {
      return "NETWORK_ERROR";
    }
  } catch (e) {
    console.error("Error fetching game categories:", e);
    if (e.response && e.response.status === 500) {
      return "NETWORK_ERROR";
    }
  }
  return null;
}

const handleLogin = async () => {
  const phoneInput = document.getElementById("loginName");
  const passwordInput = document.getElementById("user-password");
  const phone = phoneInput.value || document.getElementById("username").value;
  const password =
    passwordInput.value || document.getElementById("password").value;
  if (!phone || !password) {
    alert("Please fill in both fields");
    // return;
  } else {
    const BaseUrl = await fetchBaseURL();
    if (BaseUrl) {
      try {
        const res = await fetch(`${BaseUrl}/api/login_user`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ phone, password }),
        });
        const data = await res.json();
        console.log("Login response:", data);
        if (res.status === 200) {
          debugger;
          localStorage.setItem("token", data.token);
          // localStorage.setItem("user", JSON.stringify(data.user));
          const res =await  APIUser();
          console.log("APIUser response:", res);
          localStorage.setItem("user", JSON.stringify(res));
          // window.location.reload();
          renderAuthSection();
          if (data.message === "LOGIN_SUCCESS") {
            phoneInput.value = null;
            passwordInput.value = null;
            phone.value = "";
            password.value = "";
            closeModal();
            return data;
          } else if (data.message === "REQUIRE_RESET_PASSWORD") {
            phoneInput.value = null;
            passwordInput.value = null;
            phone.value = "";
            password.value = "";
            closeModal();
            return data;
          } else {
            phoneInput.value = null;
            passwordInput.value = null;
            phone.value = "";
            password.value = "";
            closeModal();
            return data;
          }
        }
      } catch (e) {
        console.log("Login error:", e);
        phoneInput.value = null;
        passwordInput.value = null;
        phone.value = "";
        password.value = "";
        closeModal();
        return null;
      }
      //  finally {
      //   window.location.reload();
      // }
    }
  }
  console.log("Login attempted with:", { phone, password });
  phoneInput.value = null;
  passwordInput.value = null;
  closeModal();
  // Add login logic here
};

// document.addEventListener("DOMContentLoaded", async function () {
//   try {
//     // Fetch game categories
//     const categories = await getGameCategories();
//     gameCategories =categories?.games || [];
//     console.log("gamecategories:", gameCategories);
//     // Better error handling and null checking
//     if (!categories || !categories.games) {
//       console.warn("No categories or games found");
//       return;
//     }

//     const filteredCategories = categories.games.filter((item) => item.id === 2);
//     const isLoggedIn = !!localStorage.getItem("token");
//     let html = "";
//     if (filteredCategories && filteredCategories.length > 0) {
//       filteredCategories.forEach((category) => {
//         // Added null check for game_items
//         if (category.game_items && Array.isArray(category.game_items)) {
//           category.game_items.forEach((item) => {
//             // Added fallbacks for missing data
//             const gameId = item.game_id || item.id || "";
//             const iconSrc = item.icon || "default-image.png";
//             const gameName = item.name || "Unknown Game";

//             html += `
//               <div data-distributorid="${gameId}" data-gameid="${gameId}">
//                 <img
//                   src="${iconSrc}"
//                   alt="${gameName}"
//                   width="100%"
//                   height="170px"

//                   style="border-radius: 10px; object-fit: cover;"
//                   onerror="this.src='fallback-image.png'"
//                    onclick="${isLoggedIn
//                 ? `localStorage.setItem('id', JSON.stringify('${item.game_id}')); showPointsModal('${item.game_id}');`
//                 : `showLoginModal();`
//               }"
//                   />
//               </div>
//             `;
//           });
//         }
//       });
//     } else {
//       console.warn("No categories found with id === 2");
//       // Fallback content
//       html =
//         '<div style="text-align: center; padding: 20px;">No games available at the moment.</div>';
//     }

//     const container = document.querySelector(".slick-daga-slider");
//     if (container) {
//       container.innerHTML = html;
//       if (typeof $ !== "undefined" && $.fn.slick) {
//         if ($(container).hasClass("slick-initialized")) {
//           $(container).slick("destroy");
//         }
//         $(container).slick({
//           dots: false,
//           infinite: true,
//           speed: 200,
//           slidesToShow: 1,
//           slidesToScroll: 1,
//           autoplay: false,
//           autoplaySpeed: 3000,
//           prevArrow: ".slick-prev", // Link the custom previous button
//           nextArrow: ".slick-next", // Link the custom next button
//           responsive: [
//             {
//               breakpoint: 1024,
//               settings: {
//                 slidesToShow: 2,
//                 slidesToScroll: 1,
//               },
//             },
//             {
//               breakpoint: 600,
//               settings: {
//                 slidesToShow: 1,
//                 slidesToScroll: 1,
//               },
//             },
//           ],
//         });
//       }
//     } else {
//       console.error("Slick slider container (.slick-daga-slider) not found.");
//     }
//   } catch (error) {
//     console.error("Error loading game categories:", error);

//     // Show error message in container
//     const container = document.querySelector(".slick-daga-slider");
//     if (container) {
//       container.innerHTML =
//         '<div style="text-align: center; padding: 20px; color: red;">Failed to load games. Please try again later.</div>';
//     }
//   }
// });
function closePointsModal() {
  document.getElementById("points").value = null;
  const modalOverlay = document.querySelector(".points-modal");
  const body = document.querySelector(".points-modal-body");
  if (!modalOverlay) return;
  modalOverlay.style.opacity = "0";
  modalOverlay.style.transform = "scale(0.95)";
  setTimeout(() => {
    modalOverlay.style.display = "none";
    body.style.display = "none";
  }, 200);
}

async function getBalance(id) {
  const BaseUrl = await fetchBaseURL();
  if (!BaseUrl) {
    console.error("Base URL is not defined");
    return null;
  }
  const token = localStorage.getItem("token");
  if (!token) {
    console.error("No token found in localStorage");
    return null;
  }
  return fetch(`${BaseUrl}/api/player/game/${id}/balance`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch balance");
      }
      return response.json();
    })
    .then((data) => {
      if (data && data.balance) {
        console.log("Balance fetched successfully:", data.balance);
        return data.balance;
      } else {
        console.warn("No balance data found in response");
        return 0;
      }
    })
    .catch((error) => {
      console.error("Error fetching balance:", error);
      return 0;
    });
}
function showPointsModal(id) {
  localStorage.setItem("id", JSON.stringify(id));
  const gameBalance = getBalance(id);
  console.log("Game Balance:", gameBalance);
  const modalOverlay = document.querySelector(".points-modal");
  const header = document.querySelector(".points-modal-header");
  const body = document.querySelector(".points-modal-body");
  const balance = document.getElementById("live-casino");
  balance.innerHTML = `${JSON.parse(localStorage.getItem("user")).balance}`;
  if (!modalOverlay) return;
  modalOverlay.style.display = "block";
  header.style.display = "flex";
  body.style.display = "block";
  modalOverlay.style.width = "800px";
  modalOverlay.style.opacity = "0";
  modalOverlay.style.transform = "scale(0.95)";
  setTimeout(() => {
    modalOverlay.style.opacity = "1";
    modalOverlay.style.transform = "scale(1)";
  }, 10);
}
//handle points modal
const handlePlayNow = async () => {
  console.log("handlePlayNow called");
  const points = document.getElementById("points").value;
  if (points < 150) {
    alert("Minimum transfer is 150 K");
    return;
  }

  if (points > 100000) {
    alert("Maximum transfer is 100,000 K");
    return;
  }
  let id = null;
  const idRaw = localStorage.getItem("id");
  if (idRaw !== null && idRaw !== undefined && idRaw !== "undefined") {
    try {
      id = JSON.parse(idRaw);
    } catch (e) {
      console.error("Invalid JSON in localStorage 'id':", idRaw);
      id = null;
    }
  } else if (localStorage.getItem("daga")) {
    id = localStorage.getItem("daga");
  }
  if (!id) {
    alert("Game ID not found.");
    return;
  }
  if (!points) {
    alert("Please fill in both fields");
    // return;
  } else {
    const BaseUrl = await fetchBaseURL();
    if (BaseUrl) {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch(`${BaseUrl}/api/player/game/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ game_id: id, points }),
        });
        // const data = await res.json();
        if (res.status === 200 || res.status === 201) {
          if (localStorage.getItem("daga")) {
            console.log("yes daga:", res);
            showLinksModal();
          }
          closePointsModal();
        }
      } catch (e) {
        console.log("Game login error:", e);
        points.value = null;
        closePointsModal();
        return null;
      }
    }
  }
  closePointsModal();
};

document.addEventListener("DOMContentLoaded", function () {
  const pointsInput = document.getElementById("points");
  if (pointsInput) {
    // Update on input change
    pointsInput.addEventListener("input", updatePointsDisplay);
    pointsInput.addEventListener("change", updatePointsDisplay);

    // Initialize with 0
    updatePointsDisplay();
  }
});

// Comma separator function
function addCommaSeperator(number) {
  if (number === null || number === undefined || isNaN(number)) {
    return "0";
  }
  return Number(number).toLocaleString();
}

// // Simple points conversion: 30 = 1 point
// function updatePointsDisplay(inputPoints) {
//     const realPoints = Math.trunc(inputPoints / 30) * 30; // Round down to nearest 30
//     const convertedPoints = Math.trunc(inputPoints / 30);   // How many complete points

//     // Update your existing HTML element
//     document.querySelector('.points-value.orange-text').textContent =
//         `${addCommaSeperator(realPoints)} ⬆ ${addCommaSeperator(convertedPoints)}`;
// }

function updatePointsDisplay() {
  const inputPoints = parseInt(document.getElementById("points").value) || 0;

  // Calculate conversion: 30 = 1 point
  const realPoints = Math.trunc(inputPoints / 30) * 30; // Round down to nearest 30
  const convertedPoints = Math.trunc(inputPoints / 30); // How many complete points

  // Update the result section (0 ⬆ 0)
  const resultElement = document.querySelector(
    ".result-section .points-value.orange-text"
  );
  if (resultElement) {
    resultElement.textContent = `${addCommaSeperator(
      realPoints
    )} ⬆ ${addCommaSeperator(convertedPoints)}`;
  }
}
function sliderClickHandler() {
  localStorage.setItem("daga", "daga");
  // showLinksModal();
  showPointsModal();
}

function renderGameLinks(data) {
  const linksSection = document.querySelector(".links-section");

  // Check if game links data exists
  if (data && data.length > 0) {
    let html = "";
    console.log("Rendering game links:", data);
    data.forEach((value, index) => {
      html += `
        <div class="link-item" onclick="openGameLink('${value.value}')">
          <div class="link-name-group">
            <div class="link-number">${index + 1}</div>
          </div>
          <svg class="link-icon" viewBox="0 0 24 24" fill="currentColor">
  <path d="M8.59 16.59L13.17 12L8.59 7.41L10 6L16 12L10 18L8.59 16.59Z"/>
</svg>
        </div>
      `;
    });

    // Append generated HTML to the links-section
    linksSection.innerHTML = html;
  } else {
    linksSection.innerHTML =
      '<div class="error-message">No game links available.</div>';
  }
}

function handleCopyText(fieldId) {
  const fieldElement = document.getElementById(fieldId);
  const textToCopy = fieldElement.textContent || fieldElement.innerText;
  const textArea = document.createElement("textarea");
  textArea.value = textToCopy;
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand("copy");
  document.body.removeChild(textArea);
}

async function getGameLinks() {
  const BaseUrl = await fetchBaseURL();

  if (!BaseUrl) {
    console.error("Base URL is not defined");
    return null;
  }

  try {
    const response = await fetch(`${BaseUrl}/api/website/links`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch game links");
    }

    const data = await response.json();
    console.log("Game links data:", data);

    // Pass data to render function
    renderGameLinks(data?.data);
  } catch (e) {
    console.error("Error fetching game links:", e);
    if (e.response && e.response.status === 500) {
      console.error("Server error occurred.");
    }
    document.querySelector(".links-section").innerHTML =
      '<div class="error-message text-center">Failed to load game links. Please try again later.</div>';
  }
}

showLinksModal = () => {
  const linksOverlay = document.querySelector(".links-overlay");
  document.querySelector(".close-modal-btn").style.display = "flex";
  linksOverlay.style.display = "flex";
  getGameLinks();
};

function openGameLink(link) {
  if (link) {
    console.log("Opening game link:", link);
    window.open(link, "_blank");
  }
}

async function APIUser() {
  const BaseUrl = await fetchBaseURL();
  if (!BaseUrl) {
    console.error("Base URL is not defined");
    return null;
  }

  try {
    const res = await fetch(`${BaseUrl}/api/user`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        accept: "application/json",
      },
    });

    if (res.status === 200) {
      const data = await res.json();

      // Populate the fields with data from the API
      document.getElementById("accountField").textContent =
        data.phone || "No phone available";
      document.getElementById("passwordField").textContent =
        data.raw_string || "No password available";
      document.getElementById("balanceField").textContent =
        data.balance || "No password available";
      localStorage.setItem("user", JSON.stringify(data));
      return data;
    }
  } catch (e) {
    console.error(e);
    return null;
  }
  return null;
}

document.addEventListener("DOMContentLoaded", async function () {
  getGameLinks();
  const user = await APIUser();
});
function closeModal() {
  const modalOverlay = document.querySelector(".modal-overlay");
  if (!modalOverlay) return;
  modalOverlay.style.opacity = "0";
  modalOverlay.style.transform = "scale(0.95)";
  setTimeout(() => {
    modalOverlay.style.display = "none";
  }, 200);
}

function showLoginModal() {
  console.log("showlogin modal called");
  const modalOverlay = document.querySelector(".modal-overlay");
  const header = document.querySelector(".modal-header");
  if (!modalOverlay) return;
  modalOverlay.style.display = "flex";
  header.style.display = "flex";
  modalOverlay.style.opacity = "0";
  modalOverlay.style.transform = "scale(0.95)";
  setTimeout(() => {
    modalOverlay.style.opacity = "1";
    modalOverlay.style.transform = "scale(1)";
  }, 10);
}

//hot games
document.addEventListener("hotgame-item", function () {
  const hotgameItem = document.querySelector(".hotgame-item");
  if (hotgameItem) {
    showLoginModal();
  }
});
async function getGameCategories() {
  const BaseUrl = await fetchBaseURL();
  const url = `${BaseUrl}/api/player/game_categories`;
  const token = localStorage.getItem("token") || "";
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        accept: "application/json, text/plain, */*",
        authorization: `Bearer ${token}`,
        // 'origin': 'http://localhost:3000',
        // 'referer': 'http://localhost:3000/',
      },
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Error fetching game categories:", error);
    return null;
  }
}
// const gamesList = [
//   {name: "daga", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   {name: "daga2", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   {name: "ty", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   {name: "v8", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   // {name: "daga", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   // {name: "daga", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   // {name: "daga", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   // {name: "daga", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   // {name: "daga", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   {name: "sa", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"},
//   {name: "via", icon:"./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"}
// ];
// function renderHotGames(gamesData) {
//   if (!gamesData || !gamesData.games) return;
//   const hotgameList = document.querySelector(".hotgame-list");
//   if (!hotgameList) return;

//   let html = "";
//   gamesData.games.forEach((category) => {
//     category.game_items.forEach((item) => {
//       console.log("Item:", item.icon, item.name, item.game_id);
//       // Parse name JSON
//       let nameObj = {};
//       try {
//         nameObj = JSON.parse(item.name);
//       } catch {
//         nameObj = { en: item.name, vn: item.name };
//       }
//       const isLoggedIn = !!localStorage.getItem("token");
//       html += `
//         <div class="hotgame-item" data-distributorid="${item.game_platform_id
//         }" data-gameid="${item.game_id}"
//           data-gameproviderid="${category.id}" onclick="${isLoggedIn
//           ? `localStorage.setItem('id', JSON.stringify('${item.game_id}')); showPointsModal('${item.game_id, category.id}');`
//           : `showLoginModal();`
//         }">
//           <div class="hotgame-tag">
//         <div class="tag-hot">HOT</div>
//         <div class="tag-new">NEW</div>
//           </div>
//           <div class="hotgame-img">
//         <img alt="${nameObj.vn || nameObj.en}" src="${item.icon}" />
//           </div>
//           <h3 class="hotgame-name">${nameObj.vn || nameObj.en}</h3>
//           <div class="hotgame-pd">${item.game_id}</div>
//           <div class="hover-cover">
//         <div class="hotgame-info">
//           <div class="hotgame-name">${nameObj.vn || nameObj.en}</div>
//           <div class="hotgame-pd">${item.game_id}</div>
//         </div>
//         <img alt="play icon" class="hotgame-playicon" src="images/play.png" />
//         <div class="play-btn">Chơi</div>
//           </div>
//         </div>
//       `;
//     });
//   });
//   hotgameList.innerHTML = html;
// }

// On page load, fetch and render

const gamesList = [
  {
    name: "ĐáGà 30:1",
    icon: "./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.webp",
  },
  {
    name: "ĐáGà 1:1",
    icon: "./images/e1cd97a2-28ef-4451-bb74-5cbac402b0f4.webp",
  },
  {
    name: "PM -Sports",
    icon: "./images/135db7ab-8ffb-487c-b1cf-4d5bca819f29.webp",
  },
  {
    name: "PM-ESPORT",
    icon: "./images/ef9d315b-f361-4221-83ea-7c4dca5176ec.webp",
  },
  { name: "V8", icon: "./images/b33aa54e-c36b-40ae-bd02-47ec68fac45f.webp" },
  { name: "SA", icon: "./images/92a0c5ba-f5e9-47f9-96ca-50e96ddd087e.webp" },
  { name: "Via", icon: "./images/1c6b0864-c2b9-49bb-aa46-568427525c7f.webp" },
  { name: "VIA", icon: "./images/57bdb50b-caa8-45f1-b77f-76a74135556d.webp" },
  {
    name: "Hot - Daga",
    icon: "./images/3c62b406-3b20-444a-ab51-eced3591480d.webp",
  },
  { name: "dj", icon: "./images/ed099c9c-5234-4d84-a17f-1721c1847b0d.webp" },
];

// Create a mapping function to get the correct icon based on game name
function getGameIcon(gameName) {
  const game = gamesList.find(
    (g) => g.name.toLowerCase() === gameName.toLowerCase()
  );
  return game ? game.icon : "./images/3325cd6b-4003-4f3f-b813-24cb68d175a8.png"; // fallback to default icon
}

function renderHotGames(gamesData) {
  if (!gamesData || !gamesData.games) return;
  const hotgameList = document.querySelector(".hotgame-list");
  if (!hotgameList) return;

  let html = "";
  gamesData.games.forEach((category) => {
    category.game_items.forEach((item) => {
      // console.log("Item:", item.icon, item.name, item.game_id);

      let nameObj = {};
      try {
        nameObj = JSON.parse(item.name);
      } catch {
        nameObj = { en: item.name, vn: item.name };
      }

      // Always use static icon based on game name, ignore API icon completely
      const staticIcon = getGameIcon(nameObj.en || nameObj.vn || item.name);

      const isLoggedIn = !!localStorage.getItem("token");
      html += `
        <div class="hotgame-item" data-distributorid="${
          item.game_platform_id
        }" data-gameid="${item.game_id}"
          data-gameproviderid="${category.id}" onclick="${
        isLoggedIn
          ? `localStorage.setItem('id', JSON.stringify('${
              item.game_id
            }')); showPointsModal('${(item.game_id, category.id)}');`
          : `showLoginModal();`
      }">
          <div class="hotgame-tag">
            <div class="tag-hot">HOT</div>
            <div class="tag-new">NEW</div>
          </div>
          <div class="hotgame-img">
            <img alt="${nameObj.vn || nameObj.en}" src="${staticIcon}" />
          </div>
          <h3 class="hotgame-name">${nameObj.vn || nameObj.en}</h3>
          <div class="hotgame-pd">${item.game_id}</div>
          <div class="hover-cover">
            <div class="hotgame-info">
              <div class="hotgame-name">${nameObj.vn || nameObj.en}</div>
              <div class="hotgame-pd">${item.game_id}</div>
            </div>
            <img alt="play icon" class="hotgame-playicon" src="images/play.png" />
            <div class="play-btn">Chơi</div>
          </div>
        </div>
      `;
    });
  });
  hotgameList.innerHTML = html;
}

document.addEventListener("DOMContentLoaded", async function () {
  const categories = await getGameCategories();
  renderHotGames(categories);
});

const backgroundImages = {
  0: "images/fd86b13e-cc16-4e79-b975-6f4ad0542077.jpg",
  1: "images/ff70966f-9dd1-4b35-83ad-655e6900d221.jpg",
  2: "images/40433064-908f-44cb-90f3-1367af4413f0.jpg",
  3: "images/170df58b-0899-4bfc-bce5-16938e4f27eb.jpg",
  4: "images/82c4a721-4a76-4d21-bdc7-23bae942a10a.jpg",
};

let currentIndex = 0;

function changeBackgroundImage(index) {
  const rightPanel = document.querySelector(".right");
  const imageUrl = backgroundImages[index];

  // Add fade effect
  rightPanel.style.transition = "all 0.5s ease";
  rightPanel.style.backgroundImage = `url('${imageUrl}')`;

  currentIndex = index;
}

function setActiveTab(clickedElement, index) {
  const tabs = document.querySelectorAll(".title-list > div");
  tabs.forEach((tab) => tab.classList.remove("active"));
  clickedElement.classList.add("active");
  changeBackgroundImage(index);
}
document.addEventListener("DOMContentLoaded", function () {
  const tabs = document.querySelectorAll(".title-list > div");

  tabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      const index = parseInt(this.dataset.index);
      setActiveTab(this, index);
    });
  });
  changeBackgroundImage(0);
});

document.querySelector(".handle").addEventListener("click", function () {
  document.querySelector(".event-qmenu").classList.toggle("menu-close");
});

function handleUpdateClick() {
  const updateBtn = document.querySelector(".update-btn");
  updateBtn.classList.add("spinning");
  APIUser();
  setTimeout(() => {
    updateBtn.classList.remove("spinning");
  }, 500);
}

// const user = JSON.parse(localStorage.getItem("user"));
function renderAuthSection() {
  const authSection = document.getElementById("auth-section");
  if (!authSection) {
    console.error("Element with id 'auth-section' not found in DOM.");
    return;
  }
  const token = localStorage.getItem("token");
  if (token) {
    const user = JSON.parse(localStorage.getItem("user"));
    console.log("User data:", user);
    authSection.innerHTML = `
      <nav class="user-nav">
        <ul class="nav-list">
         <li class="nav-item">${user?.name}</li>
         <li class="nav-item">${user?.balance}</li>
         <li class=" update-btn mps-update" onclick="handleUpdateClick()"></li>
          <li class="nav-item"><button class="logout-btn" onclick="logout()">Logout</button></li>
        </ul>
      </nav>
    `;
  } else {
    authSection.innerHTML = `
      <div class="input-wrap account">
        <input id="username" class="username-btn" placeholder="Tên Đăng Nhập" type="text" value="" />
      </div>
      <div class="input-wrap password">
        <input id="password" class="password-btn" placeholder="Mật Khẩu" type="password" value="" />
        
      </div>
      <div class="btn-wrap" onclick="handleLogin()">
        <div class="header-btn highlight-btn login">
          <div>Đăng nhập</div>
        </div>
      </div>
      <div class="header-btn signup" onclick="window.location.href='register.html'">
        <div>Đăng ký</div>
      </div>
      `;
  }
}
document.addEventListener("DOMContentLoaded", async function () {
  // const categories = await getGameCategories();
  renderAuthSection();
});
document.addEventListener("DOMContentLoaded", async function () {
  renderAuthSection(categories);
});

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.reload();
}

function togglePassword() {
  const passwordInput = document.getElementById("user-password");
  const toggleBtn = document.querySelector(".password-toggle");

  if (!passwordInput || !toggleBtn) return;

  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    // Eye with slash (password visible)
    toggleBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 7C14.76 7 17 9.24 17 12C17 12.65 16.87 13.26 16.64 13.83L19.56 16.75C21.07 15.49 22.26 13.86 23 12C21.27 7.61 17 4.5 12 4.5C10.6 4.5 9.26 4.75 8.04 5.2L10.17 7.33C10.74 7.13 11.35 7 12 7ZM2 4.27L4.28 6.55L4.73 7C3.08 8.3 1.78 10 1 12C2.73 16.39 7 19.5 12 19.5C13.55 19.5 15.03 19.2 16.38 18.66L16.81 19.09L19.73 22L21 20.73L3.27 3L2 4.27ZM7.53 9.8L9.08 11.35C9.03 11.56 9 11.78 9 12C9 13.66 10.34 15 12 15C12.22 15 12.44 14.97 12.65 14.92L14.2 16.47C13.53 16.8 12.79 17 12 17C9.24 17 7 14.76 7 12C7 11.21 7.2 10.47 7.53 9.8Z" fill="currentColor"/>
            </svg>`;
  } else {
    passwordInput.type = "password";
    // Eye open (password hidden)
    toggleBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 4.5C7 4.5 2.73 7.61 1 12C2.73 16.39 7 19.5 12 19.5S21.27 16.39 23 12C21.27 7.61 17 4.5 12 4.5ZM12 17C9.24 17 7 14.76 7 12S9.24 7 12 7S17 9.24 17 12S14.76 17 12 17ZM12 9C10.34 9 9 10.34 9 12S10.34 15 12 15S15 13.66 15 12S13.66 9 12 9Z" fill="currentColor"/>
            </svg>`;
  }
}

function openForgetModal() {
  closeModal(); // Close any existing modal
  const modal = document.getElementById("forgotPasswordModal");
  modal.classList.add("active");
  document.body.style.overflow = "hidden"; // Prevent background scroll
}

function closeForgetModal() {
  const modal = document.getElementById("forgotPasswordModal");
  modal.classList.remove("active");
  document.body.style.overflow = "auto"; // Restore background scroll
}

function findPassword() {
  window.open("https://direct.lc.chat/13775445/", "target= _blank");
  closeForgetModal();
}

// Close modal when clicking outside
document
  .getElementById("forgotPasswordModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeModal();
    }
  });

// Close modal with Escape key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    closeModal();
  }
});

async function renderHeaderMenus() {
  const categories = await getGameCategories();
  const isLoggedIn = !!localStorage.getItem("token");

  if (!categories || !categories.games) return;

  const navUl = document.querySelector(".main-wrap.navigation > ul.nav");
  if (!navUl) return;

  navUl.innerHTML = ""; // Clear static nav

  categories.games.forEach((category) => {
    let catNameObj = {};
    try {
      catNameObj = JSON.parse(category.name);
    } catch {
      catNameObj = { vn: category.name, en: category.name };
    }

    // Build submenu items
    let submenuHtml = "";
    if (Array.isArray(category.game_items)) {
      category.game_items.forEach((item) => {
        let itemNameObj = {};
        try {
          itemNameObj = JSON.parse(item.name);
        } catch {
          itemNameObj = { vn: item.name, en: item.name };
        }
        submenuHtml += `
         <li class="vi-VN" data-provider="${item.game_id}">
            <a data-provider="${item.game_id}" 
              onclick="${
                isLoggedIn
                  ? `localStorage.setItem('id', JSON.stringify('${item.game_id}')); showPointsModal('${item.game_id}');`
                  : `showLoginModal();`
              }"
            >
              <img alt="${
                itemNameObj.vn || itemNameObj.en
              }" loading="lazy" src="${item.icon}" />
              <span>${itemNameObj.vn || itemNameObj.en}</span>
            </a>
          </li>Z
        `;
      });
    }

    // Render category with icon
    navUl.innerHTML += `
      <li class="nav-${category.id}" data-content="${
      catNameObj.en
    }" data-title="${catNameObj.vn}">
        <div class="nav-item" 
       
        >
          <a>
            <img class="nav-icon" src="${category.icon_image}" alt="${
      catNameObj.vn || catNameObj.en
    }" style="height:24px;width:24px;vertical-align:middle;margin-right:6px;">
            <h3 style="display:inline">${catNameObj.vn || catNameObj.en}</h3>
          </a>
        </div>
        <div class="submenu">
          <ul>
            ${submenuHtml}
          </ul>
        </div>
      </li>
    `;
  });
}

// Call after DOM loaded
document.addEventListener("DOMContentLoaded", function () {
  renderHeaderMenus();
});

// function handleClick(id){
//   console.log("handleClick called with ID:", id);
//   const token = localStorage.getItem("token");
//   if (!token) {
//     showLoginModal();
//   }else {
//     // const id = JSON.parse(localStorage.getItem("id"));
//     // if (id) {
//       console.log("Game ID from localStorage:", id);
//       showPointsModal(id);
//     // } else {
//       console.error("Game ID not found in localStorage");
//     // }
//   }
// }
