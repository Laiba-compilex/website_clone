document.addEventListener('DOMContentLoaded', () => {
    const dagaContainer = document.createElement('div');
    dagaContainer.id = 'daga-banner-container';
    document.body.appendChild(dagaContainer);

    // This is a placeholder for the API call.
    // In a real application, you would fetch this data from the server.
    const gameCategories = {
        "games": [
            {
                "id": 1,
                "name": "{\"vi\":\"ĐÁ GÀ\",\"en\":\"COCK FIGHT\"}",
                "icon_image": "https://ga6789.com/storage/images/categories/icons/2023/05/19/KAiNXn21mS.png",
                "icon_active": "https://ga6789.com/storage/images/categories/icons/2023/05/19/KAiNXn21mS.png",
                "link": null,
                "game_items": [
                    {
                        "id": 1,
                        "name": "SV388",
                        "game_id": 1,
                        "game_category_id": 1,
                        "game_platform_id": "SV",
                        "icon_square": "https://ga6789.com/storage/images/games/icons/2023/05/19/SV388.png",
                        "icon_rectangle": "https://ga6789.com/storage/images/games/icons/2023/05/19/SV388.png",
                        "is_hot": 0,
                        "is_new": 0,
                        "status": 1,
                        "gameIdGetBalance": 1
                    }
                ]
            }
        ]
    };

    const dagaGame = gameCategories.games.find(game => JSON.parse(game.name).vi === 'ĐÁ GÀ');

    if (dagaGame) {
        const bannerImage = document.createElement('img');
        bannerImage.src = dagaGame.game_items[0].icon_rectangle;
        bannerImage.alt = dagaGame.game_items[0].name;
        bannerImage.style.cursor = 'pointer';
        bannerImage.addEventListener('click', () => {
            // Placeholder for opening the game modal
            alert(`Opening ${dagaGame.game_items[0].name}`);
        });
        dagaContainer.appendChild(bannerImage);
    }
});