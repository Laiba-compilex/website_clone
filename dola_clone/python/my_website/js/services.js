// const axios = require('axios');
// import JsonFormate from "./JsonFormate";
// import * as services from './index.js';
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

// On page load, fetch and render
// document.addEventListener('DOMContentLoaded', async function() {
//   const categories = await getGameCategories();
//   console.log("categories:", categories);
//   const filteredCategories = categories?.games?.filter(item => item.id === 2);

//   let html = '';
//   if (filteredCategories && filteredCategories.length > 0) {
//     filteredCategories.forEach(category => {
//       category.game_items?.forEach((item) => {
//         console.log("Item:", item.icon);
//         html += `
//           <div class="slick-daga-slider" data-distributorid="${item.game_id}" data-gameid="${item.game_id}">
//             <div>
//               <img
//                 src="${item.icon}"
//                 alt="${item.name}" width="100%" height="170px" style="border-radius: 10px;"/>
//             </div>
//           </div>
//         `;
//       });
//     });
//   }
//   // You may want to render 'html' to the DOM here, e.g.:
//   // document.getElementById('your-container-id').innerHTML = html;
// });

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
          localStorage.setItem("token", data.token);
          localStorage.setItem("user", JSON.stringify(data.user));
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
      } finally {
        window.location.reload();
      }
    }
  }
  console.log("Login attempted with:", { phone, password });
  phoneInput.value = null;
  passwordInput.value = null;
  closeModal();
  // Add login logic here
};

document.addEventListener("DOMContentLoaded", async function () {
  try {
    // Fetch game categories
    const categories = await getGameCategories();
    console.log("categories:", categories);

    // Better error handling and null checking
    if (!categories || !categories.games) {
      console.warn("No categories or games found");
      return;
    }

    const filteredCategories = categories.games.filter((item) => item.id === 2);

    let html = "";
    if (filteredCategories && filteredCategories.length > 0) {
      filteredCategories.forEach((category) => {
        // Added null check for game_items
        if (category.game_items && Array.isArray(category.game_items)) {
          category.game_items.forEach((item) => {
            console.log("Item:", item.icon);

            // Added fallbacks for missing data
            const gameId = item.game_id || item.id || "";
            const iconSrc = item.icon || "default-image.png";
            const gameName = item.name || "Unknown Game";

            html += `
              <div data-distributorid="${gameId}" data-gameid="${gameId}">
                <img
                  src="${iconSrc}"
                  alt="${gameName}" 
                  width="100%" 
                  height="170px" 
                   
                  style="border-radius: 10px; object-fit: cover;"
                  onerror="this.src='fallback-image.png'"/>
              </div>
            `;
          });
        }
      });
    } else {
      console.warn("No categories found with id === 2");
      // Fallback content
      html =
        '<div style="text-align: center; padding: 20px;">No games available at the moment.</div>';
    }

    const container = document.querySelector(".slick-daga-slider");
    if (container) {
      container.innerHTML = html;
      if (typeof $ !== "undefined" && $.fn.slick) {
        if ($(container).hasClass("slick-initialized")) {
          $(container).slick("destroy");
        }
        $(container).slick({
          dots: false,
          infinite: true,
          speed: 200,
          slidesToShow: 1,
          slidesToScroll: 1,
          autoplay: false,
          autoplaySpeed: 3000,
          prevArrow: ".slick-prev", // Link the custom previous button
          nextArrow: ".slick-next", // Link the custom next button
          responsive: [
            {
              breakpoint: 1024,
              settings: {
                slidesToShow: 2,
                slidesToScroll: 1,
              },
            },
            {
              breakpoint: 600,
              settings: {
                slidesToShow: 1,
                slidesToScroll: 1,
              },
            },
          ],
        });
      }
    } else {
      console.error("Slick slider container (.slick-daga-slider) not found.");
    }
  } catch (error) {
    console.error("Error loading game categories:", error);

    // Show error message in container
    const container = document.querySelector(".slick-daga-slider");
    if (container) {
      container.innerHTML =
        '<div style="text-align: center; padding: 20px; color: red;">Failed to load games. Please try again later.</div>';
    }
  }
});
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
function showPointsModal(id) {
  localStorage.setItem("id", JSON.stringify(id));
  const modalOverlay = document.querySelector(".points-modal");
  const header = document.querySelector(".points-modal-header");
  const body = document.querySelector(".points-modal-body");
  if (!modalOverlay) return;
  modalOverlay.style.display = "block";
  header.style.display = "block";
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

function renderHotGames(gamesData) {
  if (!gamesData || !gamesData.games) return;
  const hotgameList = document.querySelector(".hotgame-list");
  if (!hotgameList) return;

  let html = "";
  gamesData.games.forEach((category) => {
    category.game_items.forEach((item) => {
      // Parse name JSON
      let nameObj = {};
      try {
        nameObj = JSON.parse(item.name);
      } catch {
        nameObj = { en: item.name, vn: item.name };
      }
      const isLoggedIn = !!localStorage.getItem("token");
      html += `
        <div class="hotgame-item" data-distributorid="${
          item.game_platform_id
        }" data-gameid="${item.game_id}"
          data-gameproviderid="${category.id}" onclick="${
        isLoggedIn
          ? `localStorage.setItem('id', JSON.stringify('${item.game_id}')); showPointsModal('${item.game_id}');`
          : `showLoginModal();`
      }">
          <div class="hotgame-tag">
        <div class="tag-hot">HOT</div>
        <div class="tag-new">NEW</div>
          </div>
          <div class="hotgame-img">
        <img alt="${nameObj.vn || nameObj.en}" src="${item.icon}" />
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

// On page load, fetch and render
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

function renderAuthSection() {
  const authSection = document.getElementById("auth-section");
  if (!authSection) {
    console.error("Element with id 'auth-section' not found in DOM.");
    return;
  }
  const token = localStorage.getItem("token");

  if (token) {
    authSection.innerHTML = `
      <nav class="user-nav">
        <ul class="nav-list">
          <li class="nav-item"><a href="/dashboard">Deposit</a></li>
          <li class="nav-item"><a href="/profile">Withdraw Money</a></li>
          <li class="nav-item"><a href="/profile">Game History</a></li>
          <li class="nav-item"><a href="/profile">Transaction</a></li>
          <li class="nav-item"><a href="/profile">Notice</a></li>
          <li><button class="logout-btn" onclick="logout()">Logout</button></li>
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
  // const categories = await getGameCategories();
  renderAuthSection(categories);
});

function logout() {
  localStorage.removeItem("token");
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
